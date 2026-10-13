"""Price download and return computation."""
import numpy as np
import pandas as pd

from src.paths import RAW


def load_prices(ticker: str, start: str, end: str, allow_offline_fallback: bool = True):
    """Return (adjusted close Series, source name). Caches the raw download in data/raw/."""
    cache = RAW / f"{ticker.strip('^')}_{start}_{end}.csv"
    if cache.exists():
        s = pd.read_csv(cache, index_col=0, parse_dates=True).iloc[:, 0]
        return s, "yfinance"
    try:
        import yfinance as yf

        df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
        if df.empty:
            raise RuntimeError("yfinance returned no rows")
        s = df["Close"].squeeze().rename("close")
        RAW.mkdir(parents=True, exist_ok=True)
        s.to_csv(cache)
        return s, "yfinance"
    except Exception as exc:  # network blocked, rate limited, etc.
        if not allow_offline_fallback:
            raise
        print(f"[data] yfinance failed ({exc}); using arch's bundled S&P 500 copy")
        import arch.data.sp500

        s = arch.data.sp500.load()["Adj Close"].rename("close")
        return s, "offline_fallback"


def log_returns(prices: pd.Series, scale: float = 100.0) -> pd.Series:
    """Daily log returns, scaled (100 = percent). Drops the first NaN."""
    r = scale * np.log(prices).diff().dropna()
    return r.rename("ret")


def split_by_date(s: pd.Series, train_end: str, val_end: str) -> pd.Series:
    """Label each row train/val/test by calendar date. Never shuffle."""
    split = pd.Series("test", index=s.index)
    split[s.index <= val_end] = "val"
    split[s.index <= train_end] = "train"
    return split
