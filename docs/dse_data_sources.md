# DSE data access check (Phase 0, step 1)

Checked 2026-10-13.

## Verdict

**GO for daily data. NO-GO for intraday.** One condition still has to be met: a team member has to run the pull below, because this sandbox's network blocks dsebd.org, dse.com.bd, Mendeley, Kaggle and investing.com, so no real DSE rows were downloaded or inspected here.

- **DSEX:** daily closes are available from its launch on 28 Jan 2013, which gives about 13.7 years. That clears the 5 to 10 year bar. Before 2013 only the older DGEN index exists, and its method is different, so don't splice the two.
- **Stocks:** the DSE day-end archive goes back to about 1999 for long-listed names, with OHLC, previous close (`ycp`), trade count, value and volume.
- **Intraday:** there is no free intraday history. The only source found is ICE Consolidated History (tick files, history from Feb 2012), which is paid and needs a sales quote. Plan on daily data.

## Sources compared

| Source | Coverage | Frequency and fields | Adjusted? | Cost and licence | Notes |
|---|---|---|---|---|---|
| **DSE day-end archive** (old.dsebd.org `day_end_archive.php`, new dse.com.bd JSON API) | Stocks back to ~1999 | Daily: open, high, low, close, LTP, ycp, trades, value, volume | No, raw prices | Free. DSE site terms not reviewed | This is the primary source. The new API caps responses at 500 rows per page, and bdshare handles the paging |
| **DSE market summary** (`recent_market_information_more.php`) | DSEX/DS30/DSES from 2013, DGEN earlier | Daily index close plus market turnover and market cap | n/a | Free | DSEX here is close only, with no OHLC |
| **bdshare** (PyPI, MIT, v1.2.8, actively maintained) | Wraps the two sources above | Same as above | No | Free | Easiest route. `get_historical_data()` for stocks, `get_market_info_more_data()` for DSEX |
| [Mendeley: DSE Historical Data 1999–2025](https://data.mendeley.com/datasets/5mww8rb9td/1) | Jan 1999 to Apr 2025, 700+ tickers, 1.68M rows | Daily OHLCV only (no ycp) | Not stated | No licence stated | Useful for cross-checking the pull. No ycp means you can't detect bonus adjustments from it |
| [Mendeley: DSE Historical Data (23553sm4tn)](https://data.mendeley.com/datasets/23553sm4tn/3) | Not stated | Not stated | Not stated | No licence stated | Metadata is too thin to rely on |
| [KnightBase-DB](https://github.com/o-rnob/Knightbase-DB) | 1999–2026 per its README, DSEX 2013–2026 | SQLite | Only 8 tickers adjusted | MIT code, mixed data terms | The database file is missing from the repo (checked by cloning). Its README also reports a 2020–2025 gap in stock prices. Don't depend on it |
| ICE Consolidated History | From Feb 2012 | EOD, tick, Level 2 | Unknown | Paid | Only intraday option found |

Yahoo Finance, Stooq and similar free global feeds don't carry DSE.

## Data issues the cleaning stage must handle

1. **Floor-price regimes.** BSEC froze minimum prices from about Mar 2020 to Jun 2021, and again from Jul 2022 to Jan 2024 (partly lifted Dec 2022, reimposed Mar 2023). Islami Bank and Beximco stayed restricted beyond Aug 2024. During these periods many stocks print the same close with near-zero volume for months. That is roughly 2.5 of the 13.7 DSEX years. Treat them as a separate regime: either exclude them from training, or flag them and report results with and without them. Do not let flat runs count as calm periods. These dates come from press reports at month level. Confirm the exact days against BSEC orders before freezing the label rules.
2. **Unadjusted prices.** Bangladeshi firms pay bonus shares very often, so raw closes drop sharply on record dates, and those drops look like crashes. DSE resets `ycp` after a corporate action. `qc_dse.py` treats a mismatch between `ycp` and the previous close as an adjustment day and back-adjusts the series. This is an inference about how DSE sets `ycp`, so spot-check a few known bonus dates.
3. **Circuit breakers.** Daily moves are capped at about ±10%, and the lower limit was 3% for a while in 2024. Returns are truncated, which matters for GARCH tails and for the "extreme residual" labels. Days at the limit should be flagged, not treated as ordinary extremes.
4. **Holidays and halts.** Use DSEX dates as the trading calendar. The QC script counts each stock's missing days against it.
5. **Liquidity.** Thin stocks have zero-volume days. Pick the final 10 to 20 names by median daily turnover from the pulled data.

## How to pull and check (laptop or Colab)

```bash
pip install bdshare pandas numpy
python scripts/fetch_dse.py --start 2013-01-01 --out data/raw/dse      # DSEX + 20 default names
python scripts/qc_dse.py --raw data/raw/dse --out data/interim/dse_qc
```

- [fetch_dse.py](../scripts/fetch_dse.py) pulls the data in yearly chunks and keeps going if a chunk fails.
- [qc_dse.py](../scripts/qc_dse.py) writes `qc_summary.csv` with one row per series: span, missing days, zero-volume days, longest flat run, flat days inside floor periods, and moves beyond the limit. It also writes `adj_events.csv` and back-adjusted prices under `adjusted/`. I tested it on synthetic data, where it recovered an injected 20% bonus (factor 0.833), a 49-day flat run, 2 missing days and 1 zero-volume day.

The default ticker list is a starting point of large, long-listed names (GP, SQURPHARMA, BATBC, BRACBANK, RENATA, LHBL, BXPHARMA, OLYMPIC, ...). BEXIMCO and ISLAMIBANK are on it, but their floor restrictions lasted longest, so they may need to be dropped.

**Go/no-go after the pull:** the daily plan stands if DSEX has at least 3,000 rows from 2013 and at least 10 stocks have 10+ years with under 2% missing days outside floor periods.

## Fallback, if the pull fails

Use **India (NSE)**. NIFTY 50 (`^NSEI`) and the large caps (`RELIANCE.NS` and others) come through yfinance with 15+ years of split- and dividend-adjusted daily data. That's the same tooling as the global side of the project, and India is still an emerging market. India is not a frontier market like Bangladesh, though, so the transfer story gets weaker. I did not check other options here, such as Pakistan's KSE-100 or Vietnam's VN-Index.

## Licensing

I did not review DSE's website terms. The Mendeley datasets don't state a licence. Until terms are confirmed, the safest release is to publish the code and pull scripts, and not to redistribute raw DSE prices.
