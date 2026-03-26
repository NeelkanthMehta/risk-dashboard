"""
factors.py
Computes cross-sectional factor scores for each stock:
  - Momentum : 12-1 month total return (skip last month to avoid reversal)
  - Value     : inverse price-to-book (from yfinance info)
  - Size      : negative log market cap (small = high score)

All scores are z-normalised cross-sectionally.
Portfolio exposures are weight-averaged factor scores.
"""

import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st


@st.cache_data(ttl=86400, show_spinner="Computing factor scores…")
def compute_factor_exposure(prices: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    """
    Returns
    -------
    pd.DataFrame  — index = ticker, columns = ['Momentum', 'Value', 'Size',
                                                 'Composite']
    Also includes a 'Portfolio' row showing weight-averaged exposure.
    """
    tickers = prices.columns.tolist()
    records = []

    for t in tickers:
        info = {}
        try:
            info = yf.Ticker(t).fast_info
        except Exception:
            pass

        # Momentum: 252-day return, skipping last 21 trading days
        if len(prices) >= 273:
            mom = float(prices[t].iloc[-22] / prices[t].iloc[-273] - 1)
        elif len(prices) >= 22:
            mom = float(prices[t].iloc[-1] / prices[t].iloc[0] - 1)
        else:
            mom = np.nan

        # Value: 1 / P/B  (higher = cheaper)
        pb = getattr(info, "price_to_book", None)
        value = (1 / pb) if (pb and pb > 0) else np.nan

        # Size: negative log market cap (smaller = higher score)
        mc = getattr(info, "market_cap", None)
        size = (-np.log(mc)) if (mc and mc > 0) else np.nan

        records.append({"ticker": t, "Momentum": mom, "Value": value, "Size": size})

    df = pd.DataFrame(records).set_index("ticker")

    # Z-score each factor cross-sectionally
    def zscore(col):
        mu, sigma = col.mean(), col.std()
        return (col - mu) / sigma if sigma > 0 else col * 0

    for col in ["Momentum", "Value", "Size"]:
        df[col] = zscore(df[col])

    df["Composite"] = df[["Momentum", "Value", "Size"]].mean(axis=1)

    # Portfolio-level exposure row
    w = pd.Series(weights).reindex(df.index).fillna(0)
    w /= w.sum()
    port_row = (df.multiply(w, axis=0)).sum().rename("Portfolio")
    df = pd.concat([df, port_row.to_frame().T])

    return df.round(3)
