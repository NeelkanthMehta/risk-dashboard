"""
portfolio.py
Fetches OHLCV price data for a list of NSE tickers via yfinance.
Returns a DataFrame of adjusted close prices.

Uses a custom requests session with browser-like headers to avoid
Yahoo Finance rate-limiting on cloud environments (Streamlit Cloud).
"""

from datetime import date, timedelta
import pandas as pd
import requests
import yfinance as yf
import streamlit as st


def _make_session() -> requests.Session:
    """Return a requests Session that looks like a real browser."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection":      "keep-alive",
    })
    return session


@st.cache_data(ttl=3600, show_spinner="Fetching price data…")
def build_portfolio(tickers: list, lookback_days: int = 252) -> pd.DataFrame:
    """
    Parameters
    ----------
    tickers       : list of NSE tickers, e.g. ['RELIANCE.NS', 'TCS.NS']
    lookback_days : trading days of history to pull

    Returns
    -------
    prices : pd.DataFrame  — daily adjusted close, columns = tickers
    """
    end_date   = date.today()
    start_date = end_date - timedelta(days=int(lookback_days * 1.6))

    session = _make_session()

    raw = yf.download(
        tickers,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
        session=session,
    )["Close"]

    if isinstance(raw, pd.Series):
        raw = raw.to_frame(name=tickers[0])

    prices = raw.dropna(how="all").ffill()
    return prices