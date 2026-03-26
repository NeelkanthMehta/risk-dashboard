"""
factors.py
Computes cross-sectional factor scores for each stock:
  - Momentum : 12-1 month total return (skip last month)
  - Value     : inverse price-to-book (from Yahoo Finance API)
  - Size      : negative log market cap (from Yahoo Finance API)

All scores are z-normalised cross-sectionally.
Portfolio exposure is weight-averaged factor scores.
"""

import numpy as np
import pandas as pd
import requests
import streamlit as st

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def _fetch_fundamentals(ticker: str) -> dict:
    """Fetch key stats from Yahoo Finance quoteSummary API."""
    url = (
        f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{ticker}"
        f"?modules=defaultKeyStatistics,summaryDetail"
    )
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        data    = resp.json()["quoteSummary"]["result"][0]
        stats   = data.get("defaultKeyStatistics", {})
        summary = data.get("summaryDetail", {})

        pb  = summary.get("priceToBook",  {}).get("raw", None)
        mc  = stats.get("marketCap",      {}).get("raw", None)
        return {"price_to_book": pb, "market_cap": mc}
    except Exception:
        return {"price_to_book": None, "market_cap": None}


@st.cache_data(ttl=86400, show_spinner="Computing factor scores…")
def compute_factor_exposure(prices: pd.DataFrame, weights: dict) -> pd.DataFrame:
    """
    Returns
    -------
    pd.DataFrame — index = ticker, columns = ['Momentum', 'Value', 'Size', 'Composite']
    Includes a 'Portfolio' row showing weight-averaged exposure.
    """
    tickers = prices.columns.tolist()
    records = []

    for t in tickers:
        # Momentum: 252-day return skipping last 21 days
        if len(prices) >= 273:
            mom = float(prices[t].iloc[-22] / prices[t].iloc[-273] - 1)
        elif len(prices) >= 22:
            mom = float(prices[t].iloc[-1] / prices[t].iloc[0] - 1)
        else:
            mom = np.nan

        # Fundamentals from Yahoo Finance API
        info  = _fetch_fundamentals(t)
        pb    = info["price_to_book"]
        mc    = info["market_cap"]
        value = (1 / pb)        if (pb and pb > 0)  else np.nan
        size  = (-np.log(mc))   if (mc and mc > 0)  else np.nan

        records.append({"ticker": t, "Momentum": mom, "Value": value, "Size": size})

    df = pd.DataFrame(records).set_index("ticker")

    def zscore(col):
        mu, sigma = col.mean(), col.std()
        return (col - mu) / sigma if sigma > 0 else col * 0

    for col in ["Momentum", "Value", "Size"]:
        df[col] = zscore(df[col])

    df["Composite"] = df[["Momentum", "Value", "Size"]].mean(axis=1)

    # Portfolio-level exposure row
    w = pd.Series(weights).reindex(df.index).fillna(0)
    w /= w.sum()
    port_row = df.multiply(w, axis=0).sum().rename("Portfolio")
    df = pd.concat([df, port_row.to_frame().T])

    return df.round(3)