# First GARCH run: findings

**Data used:** S&P 500 adjusted close, 1999-01-05 to 2018-12-31 (5,030 returns). Yahoo Finance was unreachable from the cloud sandbox, so the script fell back to the copy bundled with the `arch` package. On your laptop/Colab it will pull ^GSPC 2010 to 2025 from yfinance with the date splits in `config.yaml`.

**Splits (by date):** train 1999 to 2012 (3,520 days, includes 2008), val 2013 to 2015 (756), test 2016 to 2018 (754).

## Model fit on train (Student-t errors)

| Model | Log-lik | BIC | Persistence | Leverage | t dof |
|---|---|---|---|---|---|
| GARCH(1,1) | -5230.7 | 10502.1 | α+β = 0.996 | n/a | 8.3 |
| EGARCH(1,1,1) | -5159.7 | **10368.5** | β = 0.986 | γ = -0.137 | 9.5 |
| GJR(1,1,1) | -5165.8 | 10380.6 | α+β+γ/2 = 0.991 | γ = 0.142, α ≈ 0 | 10.4 |

Both asymmetric models beat plain GARCH by about 120 BIC points: negative shocks raise volatility much more than positive ones. GJR's α is essentially zero, so in that model only down days feed volatility.

## Residual adequacy (p-values, >0.05 means no leftover structure)

| Model / block | LB z (10) | LB z² (10) | ARCH-LM (10) |
|---|---|---|---|
| GARCH train / val / test | 0.03 / 0.34 / 0.59 | 0.004 / 0.004 / 0.12 | 0.005 / 0.009 / 0.13 |
| EGARCH train / val / test | 0.02 / 0.34 / 0.25 | 0.001 / 0.23 / **<1e-9** | 0.001 / 0.21 / **<1e-6** |
| GJR train / val / test | 0.06 / 0.36 / 0.58 | 0.008 / 0.50 / 0.35 | 0.008 / 0.42 / 0.37 |

- On train, all three leave a little ARCH structure (p < 0.01). That is common with a sample containing 2008; a richer spec (e.g. GARCH(2,1) or a skewed-t) may clear it.
- **The BIC winner (EGARCH) is the worst out of sample:** on the 2016 to 2018 test block its squared residuals are strongly autocorrelated. GJR passes on val and test. Lesson for the paper: select the volatility model on validation diagnostics, not training BIC alone.
- Jarque-Bera rejects normality everywhere (expected; that is why Student-t is used).

## First-look statistical labels

Rule: flag a day if |z| exceeds the fitted Student-t two-sided 0.2% cutoff (|z| > 3.75 for EGARCH). Compared with a naive z-score on raw returns using the same tail probability (|z| > 3.09).

| | Flags | Share in busiest 3 years |
|---|---|---|
| Raw-return z-score | 54 | 76% (25 of them in 2008 alone) |
| GARCH-standardized | 17 | 47% |

Top GARCH flags line up with known events: 2007-02-27 (Shanghai sell-off), 2016-06-24 (Brexit), 2018-02-05 (volatility spike), 2018-10-10, 2008-09-29 (TARP vote). Raw z-scores miss most of these because they happened in calm periods.

**Caveat:** 7 of the 17 GARCH flags fall in the 754 test days, where about 1.5 would be expected. With parameters frozen since 2012, the model underestimates how low volatility got in 2017, so ordinary moves look extreme. This is the leakage-safe setup working as intended, and it shows why Phase 2 needs rolling or expanding re-fits before freezing statistical labels.

## Next steps this suggests
1. Add an expanding-window re-fit (e.g. yearly) and compare flag counts on test.
2. Try GJR as the default volatility model; re-check on DSE data.
3. Draft `docs/labeling_rules.md` (threshold, event list, injection protocol) and freeze it before Phase 3.
