"""
returns.py
Computes individual and weighted portfolio log-returns.
"""

import numpy as np
import pandas as pd


def compute_returns(prices: pd.DataFrame, weights: dict[str, float]) -> dict:
    """
    Parameters
    ----------
    prices  : adjusted close DataFrame (tickers as columns)
    weights : {ticker: weight} — must sum to 1.0

    Returns
    -------
    dict with keys:
      'stocks'    — pd.DataFrame of individual daily log-returns
      'portfolio' — pd.Series of weighted daily log-returns
      'cum_stocks'    — pd.DataFrame cumulative returns per stock
      'cum_portfolio' — pd.Series cumulative portfolio return
    """
    log_ret = np.log(prices / prices.shift(1)).dropna()

    w = pd.Series(weights).reindex(log_ret.columns).fillna(0)
    w /= w.sum()                                         # normalise defensively

    port_ret = log_ret.dot(w)

    return {
        "stocks":         log_ret,
        "portfolio":      port_ret,
        "cum_stocks":     log_ret.cumsum().apply(np.exp) - 1,
        "cum_portfolio":  port_ret.cumsum().apply(np.exp) - 1,
        "weights":        w,
    }
