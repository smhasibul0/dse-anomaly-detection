"""First end-to-end GARCH workflow on a global index.

Usage (from the repo root):  python scripts/01_first_garch.py
Writes tables and a figure to reports/first_garch/ and the filtered series
to data/processed/.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data import load_prices, log_returns, split_by_date  # noqa: E402
from src.paths import PROCESSED  # noqa: E402
from src.garch import diagnostics, fit_on_train, std_t_threshold  # noqa: E402
from src.seeds import set_seed  # noqa: E402

cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
set_seed(cfg["seed"])
OUT = ROOT / "reports" / "first_garch"
OUT.mkdir(parents=True, exist_ok=True)

# 1. Data ---------------------------------------------------------------
d = cfg["data"]
prices, source = load_prices(d["ticker"], d["start"], d["end"], d["allow_offline_fallback"])
ret = log_returns(prices, cfg["garch"]["returns_scale"])
sp = cfg["splits"][source]
split = split_by_date(ret, sp["train_end"], sp["val_end"])
is_train = split == "train"
print(f"[data] source={source}  {ret.index[0].date()} to {ret.index[-1].date()}  n={len(ret)}")
print(split.value_counts().reindex(["train", "val", "test"]).to_string())

# 2. Fit the three GARCH variants on train only -------------------------
g = cfg["garch"]
rows, diag_rows, fits = [], [], {}
for name in g["models"]:
    tr, full = fit_on_train(ret, is_train, name, g["mean"], g["dist"])
    fits[name] = (tr, full)
    z = full.std_resid
    rows.append({"model": name, "loglik": tr.loglikelihood, "AIC": tr.aic, "BIC": tr.bic,
                 **{k: v for k, v in tr.params.items()}})
    for blk in ["train", "val", "test"]:
        diag_rows.append({"model": name, "block": blk, **diagnostics(z[split == blk], g["diag_lags"])})

params = pd.DataFrame(rows).set_index("model")
diag = pd.DataFrame(diag_rows).set_index(["model", "block"])
params.to_csv(OUT / "params_train.csv")
diag.to_csv(OUT / "residual_diagnostics.csv")
pd.set_option("display.width", 200, "display.precision", 4)
print("\n[fit] training-split estimates\n", params)
print("\n[diag] p-values (> 0.05 = no evidence of leftover structure)\n", diag)

# 3. Pick the model with the lowest training BIC ------------------------
best = params["BIC"].idxmin()
tr, full = fits[best]
nu = float(tr.params["nu"])
z = full.std_resid.rename("z")
vol = full.conditional_volatility.rename("cond_vol")

# 4. First-look statistical flags ---------------------------------------
tp = cfg["labels_first_look"]["tail_prob"]
thr_garch = std_t_threshold(nu, tp)
mu, sd = ret[is_train].mean(), ret[is_train].std()
z_raw = ((ret - mu) / sd).rename("z_raw")       # naive baseline: no volatility model
thr_raw = float(stats.norm.ppf(1 - tp / 2))

flags = pd.DataFrame({"ret": ret, "z": z, "z_raw": z_raw, "cond_vol": vol, "split": split})
flags["flag_garch"] = flags["z"].abs() > thr_garch
flags["flag_raw"] = flags["z_raw"].abs() > thr_raw
PROCESSED.mkdir(parents=True, exist_ok=True)
flags.to_csv(PROCESSED / f"{d['ticker'].strip('^')}_{best}_filtered.csv")
flags[flags.flag_garch].sort_values("z", key=abs, ascending=False).to_csv(OUT / "flagged_days_garch.csv")

by_year = flags.groupby(flags.index.year)[["flag_garch", "flag_raw"]].sum()
by_year.to_csv(OUT / "flags_per_year.csv")
expected = tp * len(flags)
summary = {
    "source": source, "best_model_by_BIC": best, "nu": nu,
    "thr_garch_|z|": thr_garch, "thr_raw_|z|": thr_raw,
    "n_days": len(flags), "expected_flags_if_model_exact": expected,
    "n_flag_garch": int(flags.flag_garch.sum()), "n_flag_raw": int(flags.flag_raw.sum()),
    "flag_raw_share_in_top3_years": float(by_year.flag_raw.nlargest(3).sum() / max(by_year.flag_raw.sum(), 1)),
    "flag_garch_share_in_top3_years": float(by_year.flag_garch.nlargest(3).sum() / max(by_year.flag_garch.sum(), 1)),
}
pd.Series(summary).to_csv(OUT / "summary.csv", header=["value"])
print("\n[labels] summary\n", pd.Series(summary).to_string())
print("\n[labels] flags per year\n", by_year.T.to_string())

# 5. Figure -------------------------------------------------------------
fig, ax = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
colors = {"train": "#f2f2f2", "val": "#e3ecf7", "test": "#fbe9e2"}
for a in ax:
    for blk, c in colors.items():
        idx = flags.index[flags.split == blk]
        a.axvspan(idx[0], idx[-1], color=c, zorder=0, label=blk)
ax[0].plot(ret, lw=0.5, color="#333")
ax[0].plot(flags.ret[flags.flag_raw], "o", ms=3, color="#c0392b", label="raw |z| flag")
ax[0].set_ylabel("log return (%)")
ax[0].set_title(f"S&P 500 daily returns, raw z-score flags ({int(flags.flag_raw.sum())})")
ax[0].legend(loc="lower left", ncol=4, fontsize=8)
ax[1].plot(vol, lw=0.8, color="#1f5fa8")
ax[1].set_ylabel("cond. vol (%)")
ax[1].set_title(f"{best}(1,1) conditional volatility, params frozen from train")
ax[2].plot(z, lw=0.5, color="#333")
ax[2].plot(flags.z[flags.flag_garch], "o", ms=3, color="#c0392b")
for s in (1, -1):
    ax[2].axhline(s * thr_garch, ls="--", lw=0.8, color="#c0392b")
ax[2].set_ylabel("standardized resid")
ax[2].set_title(f"GARCH-standardized residuals, |z| > {thr_garch:.2f} flags ({int(flags.flag_garch.sum())})")
fig.tight_layout()
fig.savefig(OUT / "first_garch.png", dpi=130)
print(f"\n[done] outputs in {OUT.relative_to(ROOT)}")
