# Volatility-aware anomaly detection: global markets to DSE

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/smhasibul0/dse-anomaly-detection/blob/main/notebooks/00_colab_setup.ipynb)

Starter repo for the project *Volatility-Aware Deep Anomaly Detection for Emerging-Market Stocks: Transfer from Global Markets to the Dhaka Stock Exchange*.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/01_first_garch.py
```

### Colab

Click the badge above, or open `notebooks/00_colab_setup.ipynb` in Colab. Set `REPO_URL` in the first cell. For a private repo, also add a GitHub token as a Colab secret named `GITHUB_TOKEN`. Then run all cells. The notebook clones the repo, installs requirements, fixes the seed, mounts Google Drive, pulls and checks the DSE data, and runs the first GARCH fit on `^GSPC`.

Data is kept in `MyDrive/dse-anomaly/data/` so it survives between sessions. Scripts find it through the `PROJECT_DATA_DIR` environment variable. Without that variable, they use `./data`.

## Layout

```
config.yaml           all run settings (seed, dates, splits, GARCH options)
data/raw|interim|processed   see data/README.md; data is not committed
src/paths.py          data location (PROJECT_DATA_DIR or ./data)
src/seeds.py          set_seed() and rng(); see docs/seed_policy.md
src/data.py           download (yfinance, with offline fallback), log returns, time splits
src/garch.py          GARCH / EGARCH / GJR fit on train, frozen-param filter, diagnostics
scripts/fetch_dse.py  pull DSEX + DSE stocks (bdshare, unadjusted)
scripts/qc_dse.py     DSE quality report, bonus-adjustment detection, back-adjusted prices
scripts/01_first_garch.py   first end-to-end GARCH run
reports/              tables and figures written by scripts
literature/literature_review.csv   shared reading table
docs/                 seed policy, DSE data sources (and, next, the frozen labeling rules)
notebooks/00_colab_setup.ipynb   Colab entry point
notebooks/            otherwise exploration only; anything reused moves to src/
```

## What `01_first_garch.py` does

1. Downloads S&P 500 daily prices (yfinance, adjusted close) and computes percent log returns.
2. Splits **by date** into train / val / test (dates in `config.yaml`).
3. Fits GARCH(1,1), EGARCH(1,1,1) and GJR-GARCH(1,1,1) with Student-t errors **on train only**.
4. Runs the whole series through each model with the **training parameters frozen**, so val/test volatility never uses future data.
5. Residual checks per block: Ljung-Box on z and z² (lags 10, 20), ARCH-LM (lag 10), Jarque-Bera.
6. Picks the lowest-BIC model and flags days where |z| exceeds the fitted Student-t two-sided 0.2% cutoff. Compares with a naive raw-return z-score using the same tail probability.

Outputs land in `reports/first_garch/` and `data/processed/`.

## Leakage rules (project-wide)

- Split by time, never randomly.
- Fit GARCH (and any scaler, threshold or normaliser) on train only.
- When scoring later periods, use rolling or expanding re-fits that only see past data.
- Write labeling rules in `docs/labeling_rules.md` and freeze them **before** training any detector.

## Team ownership (from the plan)

- Member 1: data collection, cleaning, labels
- Member 2: GARCH modelling and baselines
- Member 3: deep models, transfer experiments
