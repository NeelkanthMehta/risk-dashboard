"""
portfolio.py
Fetches OHLCV price data for a list of NSE tickers via yfinance.
"""

from datetime import date, timedelta
import pandas as pd
import yfinance as yf
import streamlit as st


@st.cache_data(ttl=3600, show_spinner="Fetching price data…")
def build_portfolio(tickers: list, lookback_days: int = 252) -> pd.DataFrame:
    end_date   = date.today()
    start_date = end_date - timedelta(days=int(lookback_days * 1.6))

    raw = yf.download(
        tickers,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
        group_by="ticker",
    )

    # Handle both flat and MultiIndex column structures
    if isinstance(raw.columns, pd.MultiIndex):
        # New yfinance: columns are (ticker, field) — extract Close for each
        frames = {}
        for t in tickers:
            try:
                frames[t] = raw[t]["Close"]
            except KeyError:
                pass
        prices = pd.DataFrame(frames)
    else:
        prices = raw["Close"] if "Close" in raw.columns else raw

    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=tickers[0])

    # Drop rows where ALL tickers are NaN, then forward-fill gaps
    prices = prices.dropna(how="all").ffill().dropna(how="all")
    return prices