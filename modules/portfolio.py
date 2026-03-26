"""
portfolio.py
Fetches daily close prices directly from Yahoo Finance query2 API.
No yfinance dependency — plain requests to avoid cloud rate-limit issues.
"""

from datetime import date, timedelta
import time
import pandas as pd
import requests
import streamlit as st

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def _fetch_ticker(ticker: str, start: date, end: date) -> pd.Series:
    """Fetch daily adjusted close for a single ticker from Yahoo Finance API."""
    start_ts = int(time.mktime(start.timetuple()))
    end_ts   = int(time.mktime(end.timetuple()))

    url = (
        f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
        f"?period1={start_ts}&period2={end_ts}&interval=1d&adjclose=true"
    )
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        chart    = data["chart"]["result"][0]
        timestamps = chart["timestamp"]
        adjclose   = chart["indicators"]["adjclose"][0]["adjclose"]

        dates  = pd.to_datetime(timestamps, unit="s").normalize()
        series = pd.Series(adjclose, index=dates, name=ticker, dtype=float)
        return series.dropna()

    except Exception:
        return pd.Series(name=ticker, dtype=float)


@st.cache_data(ttl=3600, show_spinner="Fetching price data…")
def build_portfolio(tickers: list, lookback_days: int = 252) -> pd.DataFrame:
    """
    Parameters
    ----------
    tickers       : list of NSE tickers, e.g. ['RELIANCE.NS', 'TCS.NS']
    lookback_days : trading days of history to pull

    Returns
    -------
    prices : pd.DataFrame — daily adjusted close, columns = tickers
    """
    end_date   = date.today()
    start_date = end_date - timedelta(days=int(lookback_days * 1.6))

    series_list = [_fetch_ticker(t, start_date, end_date) for t in tickers]
    prices = pd.concat(series_list, axis=1)
    prices = prices[~prices.index.duplicated(keep='last')]
    prices = prices.sort_index()
    prices = prices.ffill().dropna(how="all")
    return prices