"""GARCH-family fitting and residual diagnostics.

Leakage rule: parameters are estimated on the training block only. Val/test
volatility is produced by running the fixed training parameters forward through
the full series (a one-step-ahead filter), so no future data touches estimation.
"""
import warnings

import numpy as np
import pandas as pd
from arch import arch_model
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch

SPECS = {
    "GARCH": dict(vol="GARCH", p=1, o=0, q=1),
    "EGARCH": dict(vol="EGARCH", p=1, o=1, q=1),
    "GJR": dict(vol="GARCH", p=1, o=1, q=1),  # o=1 adds the GJR leverage term
}


def fit_on_train(ret: pd.Series, is_train: pd.Series, name: str, mean="Constant", dist="t"):
    """Fit on train rows, then filter the whole series with the frozen params."""
    spec = SPECS[name]
    train_res = arch_model(ret[is_train], mean=mean, dist=dist, **spec).fit(disp="off")
    full_model = arch_model(ret, mean=mean, dist=dist, **spec)
    full_res = full_model.fix(train_res.params)
    return train_res, full_res


def diagnostics(std_resid: pd.Series, lags=(10, 20)) -> dict:
    """Ljung-Box on z and z^2, ARCH-LM on z. Large p-values = model adequate."""
    z = std_resid.dropna()
    out = {}
    lb = acorr_ljungbox(z, lags=list(lags))
    lb2 = acorr_ljungbox(z**2, lags=list(lags))
    for L in lags:
        out[f"LB_z_p@{L}"] = lb.loc[L, "lb_pvalue"]
        out[f"LB_z2_p@{L}"] = lb2.loc[L, "lb_pvalue"]
    with warnings.catch_warnings():  # statsmodels 0.15 return-type FutureWarning
        warnings.simplefilter("ignore", FutureWarning)
        lm_stat, lm_p, _, _ = het_arch(z, nlags=lags[0])
    out[f"ARCH_LM_p@{lags[0]}"] = lm_p
    out["JB_p"] = stats.jarque_bera(z).pvalue
    out["mean_z"] = z.mean()
    out["std_z"] = z.std()
    return out


def std_t_threshold(nu: float, tail_prob: float) -> float:
    """|z| cutoff for a two-sided tail prob under a unit-variance Student-t."""
    q = stats.t.ppf(1 - tail_prob / 2, df=nu)
    return float(q * np.sqrt((nu - 2) / nu))
