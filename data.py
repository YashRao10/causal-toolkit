"""Generic daily-price data pull for any set of tickers.

yfinance-only data layer, generalized to
take tickers/start date as arguments instead of hardcoding one event's
universe.
"""
from __future__ import annotations

import pandas as pd
import yfinance as yf


def fetch_daily_levels(tickers: list[str], start: str) -> pd.DataFrame:
    """Download daily closes (dividend/split-adjusted) and rebase each ticker to 100 at `start`.

    Drops any row with data missing for even one ticker (`how="any"`, not
    `"all"`) — a partial row would otherwise silently corrupt every
    downstream calculation that touches it (NaN propagates through the
    weight fit and the reported gap) rather than just being absent.
    """
    raw = yf.download(tickers, start=start, progress=False, auto_adjust=True)["Close"]
    raw = raw.dropna(how="any")
    rebased = raw / raw.iloc[0] * 100
    return rebased
