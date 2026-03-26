"""
portfolio.py
Fetches OHLCV price data for a list of NSE tickers via yfinance.
Returns a DataFrame of adjusted close prices.
"""

from datetime import date, timedelta
import pandas as pd
import yfinance as yf
import streamlit as st


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

    raw = yf.download(
        tickers,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
    )["Close"]

    if isinstance(raw, pd.Series):
        raw = raw.to_frame(name=tickers[0])

    prices = raw.dropna(how="all").ffill()

    return prices