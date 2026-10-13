# Data layout

| Folder | What goes here | Who writes it | In git? |
|---|---|---|---|
| `raw/` | Untouched downloads exactly as received (yfinance CSVs, DSE files). Never edited by hand. | `src/data.py` / scrapers | No |
| `interim/` | Cleaned but not final: calendar-aligned, halts and splits handled, DSE price-limit days marked. | Member 1 cleaning scripts | No |
| `processed/` | Model-ready tables: returns, GARCH volatility, standardized residuals, labels, split column. | Pipeline scripts | No |

Rules
- Every file in `interim/` and `processed/` must be reproducible from `raw/` by a script in `scripts/`.
- File names: `<MARKET>_<TICKER>_<what>.csv`, e.g. `DSE_DSEX_returns.csv`, `US_GSPC_EGARCH_filtered.csv`.
- Keep a short note in this README for each new raw source: where it came from, date pulled, licence/terms.

Raw source log
- DSE: see `docs/dse_data_sources.md`. Pulled with `scripts/fetch_dse.py` into `raw/dse/`; QC output in `interim/dse_qc/`.
- `^GSPC` daily, yfinance, adjusted close. (In the first cloud run Yahoo was unreachable, so the script fell back to the S&P 500 copy shipped with the `arch` package, 1999 to 2018.)
