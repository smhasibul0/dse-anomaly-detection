"""Quality report for CSVs written by fetch_dse.py.

    python qc_dse.py --raw data/raw/dse --out data/qc

Writes qc_summary.csv (one row per series), adj_events.csv (days where DSE's
ycp differs from the previous close, i.e. likely bonus/rights/split
adjustments) and adjusted/<SYM>.csv with back-adjusted prices.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# Approximate floor-price regimes (month-level from press reports; confirm
# exact days against BSEC orders before using them in labels or splits).
FLOOR_PERIODS = [("2020-03-19", "2021-06-17"), ("2022-07-28", "2024-01-18")]
LIMIT = 0.10  # DSE circuit breaker is roughly +/-10% for most price bands


def longest_run(mask):
    best = cur = 0
    for m in mask:
        cur = cur + 1 if m else 0
        best = max(best, cur)
    return best


def in_floor(dates):
    m = pd.Series(False, index=dates.index)
    for a, b in FLOOR_PERIODS:
        m |= (dates >= a) & (dates <= b)
    return m


def check_stock(sym, df, calendar):
    df = df.sort_values("date").reset_index(drop=True)
    prev_close = df["close"].shift(1)
    ret = np.log(df["close"] / prev_close)
    # DSE resets ycp after corporate actions; a mismatch with the prior close
    # marks an adjustment day. factor < 1 means a bonus/split diluted the price.
    factor = df["ycp"] / prev_close
    # Mask before assigning: assigning a full-length Series to an empty frame
    # would re-expand it to every row and miscount stocks with no events.
    adj = df.assign(symbol=sym, factor=factor)[(factor - 1).abs() > 0.01]
    # Returns measured against ycp strip those mechanical jumps out.
    adj_ret = np.log(df["close"] / df["ycp"])
    cum = factor.where((factor - 1).abs() > 0.01, 1.0).fillna(1.0)
    back = cum[::-1].cumprod()[::-1].shift(-1).fillna(1.0)  # apply to earlier rows
    adjusted = df.assign(adj_factor=back)
    for c in ["open", "high", "low", "close", "ltp", "ycp"]:
        adjusted[f"adj_{c}"] = df[c] * back
    span = calendar[(calendar >= df["date"].min()) & (calendar <= df["date"].max())]
    floor = in_floor(df["date"])
    row = {
        "series": sym,
        "first": df["date"].min().date(),
        "last": df["date"].max().date(),
        "rows": len(df),
        "years": round((df["date"].max() - df["date"].min()).days / 365.25, 1),
        "missing_vs_calendar": int((~span.isin(df["date"])).sum()),
        "zero_volume_days": int((df["volume"] == 0).sum()),
        "longest_flat_close_run": longest_run(df["close"].diff().eq(0)),
        "flat_days_in_floor": int((df["close"].diff().eq(0) & floor).sum()),
        "abs_raw_ret_gt_limit": int((ret.abs() > np.log(1 + LIMIT) + 0.005).sum()),
        "abs_ycp_ret_gt_limit": int((adj_ret.abs() > np.log(1 + LIMIT) + 0.005).sum()),
        "adj_events": len(adj),
        "median_daily_value_mn": round(df["value"].median(), 2),
    }
    return row, adj[["symbol", "date", "close", "ycp", "factor"]], adjusted


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw/dse")
    ap.add_argument("--out", default="data/qc")
    args = ap.parse_args()
    raw, out = Path(args.raw), Path(args.out)
    (out / "adjusted").mkdir(parents=True, exist_ok=True)

    rows, events = [], []
    dsex_path = raw / "dsex.csv"
    calendar = None
    if dsex_path.exists():
        dsex = pd.read_csv(dsex_path, parse_dates=["date"]).sort_values("date")
        calendar = dsex["date"]
        s = dsex.set_index("date")["DSEX Index"].replace(0, np.nan)
        r = np.log(s).diff()
        gaps = calendar.diff().dt.days
        rows.append({
            "series": "DSEX",
            "first": calendar.min().date(),
            "last": calendar.max().date(),
            "rows": len(dsex),
            "years": round((calendar.max() - calendar.min()).days / 365.25, 1),
            "missing_vs_calendar": int(s.isna().sum()),
            "longest_flat_close_run": longest_run(s.diff().eq(0)),
            "max_calendar_gap_days": int(gaps.max()),
            "abs_raw_ret_gt_limit": int((r.abs() > np.log(1 + LIMIT)).sum()),
        })

    stocks = {p.stem: pd.read_csv(p, parse_dates=["date"]) for p in sorted(raw.glob("*.csv"))
              if p.stem != "dsex"}
    if calendar is None:  # fall back to the union of stock trading days
        calendar = pd.Series(sorted(set().union(*[set(d["date"]) for d in stocks.values()])))
    for sym, df in stocks.items():
        row, adj, adjusted = check_stock(sym, df, calendar)
        rows.append(row)
        events.append(adj)
        adjusted.to_csv(out / "adjusted" / f"{sym}.csv", index=False)

    summary = pd.DataFrame(rows)
    summary.to_csv(out / "qc_summary.csv", index=False)
    if events:
        pd.concat(events).to_csv(out / "adj_events.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
