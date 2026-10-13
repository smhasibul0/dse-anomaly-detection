"""Pull DSEX index and liquid DSE stock history from the DSE day-end archive.

Run on a laptop or Colab (needs access to dsebd.org):
    pip install bdshare pandas
    python fetch_dse.py --start 2013-01-01 --end 2026-10-12 --out data/raw/dse

Writes one CSV per symbol plus dsex.csv. Prices are UNADJUSTED; see qc_dse.py
for adjustment factors estimated from DSE's ycp field.
"""
import argparse
import time
from pathlib import Path

import pandas as pd
from bdshare import get_historical_data, get_market_info_more_data

# Starting list: large, long-listed DSE names (mostly DS30 members). Confirm
# liquidity from the pulled turnover before fixing the final universe.
DEFAULT_SYMBOLS = [
    "GP", "SQURPHARMA", "BATBC", "BEXIMCO", "BRACBANK", "RENATA", "LHBL",
    "BXPHARMA", "ISLAMIBANK", "OLYMPIC", "UPGDCL", "SUMITPOWER", "MARICO",
    "CITYBANK", "DUTCHBANGL", "BSRMLTD", "ACI", "POWERGRID", "TITASGAS",
    "SINGERBD",
]


def year_chunks(start, end):
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    cur = s
    while cur <= e:
        nxt = min(pd.Timestamp(year=cur.year, month=12, day=31), e)
        yield cur.strftime("%Y-%m-%d"), nxt.strftime("%Y-%m-%d")
        cur = nxt + pd.Timedelta(days=1)


def fetch_chunked(fn, start, end, pause, **kw):
    parts = []
    for a, b in year_chunks(start, end):
        try:
            df = fn(a, b, **kw)
            if df is not None and len(df):
                parts.append(df.reset_index())
            print(f"  {a}..{b}: {0 if df is None else len(df)} rows")
        except Exception as exc:  # keep going; gaps are reported by qc_dse.py
            print(f"  {a}..{b}: FAILED {exc}")
        time.sleep(pause)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2013-01-01")
    ap.add_argument("--end", default=pd.Timestamp.today().strftime("%Y-%m-%d"))
    ap.add_argument("--out", default="data/raw/dse")
    ap.add_argument("--symbols", nargs="*", default=DEFAULT_SYMBOLS)
    ap.add_argument("--pause", type=float, default=1.0, help="seconds between requests")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    print("DSEX (market summary, close only)")
    idx = fetch_chunked(get_market_info_more_data, args.start, args.end, args.pause)
    if len(idx):
        idx = idx.rename(columns={"Date": "date"})
        idx["date"] = pd.to_datetime(idx["date"])
        idx = idx.drop_duplicates("date").sort_values("date")
        idx.to_csv(out / "dsex.csv", index=False)

    for sym in args.symbols:
        print(sym)
        df = fetch_chunked(get_historical_data, args.start, args.end, args.pause, code=sym)
        if not len(df):
            continue
        df["date"] = pd.to_datetime(df["date"])
        df = df.drop_duplicates("date").sort_values("date")
        df.to_csv(out / f"{sym}.csv", index=False)


if __name__ == "__main__":
    main()
