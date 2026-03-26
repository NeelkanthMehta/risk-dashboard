"""
correlation.py
Computes a rolling Pearson correlation matrix across portfolio constituents.
Returns the most recent window's snapshot for heatmap display,
plus the full rolling series for a chosen pair.
"""

import numpy as np
import pandas as pd


def rolling_correlation(
    stock_returns: pd.DataFrame,
    window: int = 60,
) -> dict:
    """
    Parameters
    ----------
    stock_returns : pd.DataFrame of individual stock log-returns
    window        : rolling lookback in trading days

    Returns
    -------
    dict with keys:
      'matrix'        — pd.DataFrame, latest correlation matrix
      'rolling_mean'  — pd.Series, mean pairwise correlation over time
    """
    corr_matrix = stock_returns.tail(window).corr()

    # Rolling mean pairwise correlation (excluding diagonal)
    roll_corr = (
        stock_returns.rolling(window)
        .corr()
        .groupby(level=0)
        .apply(lambda m: m.values[~np.eye(len(m), dtype=bool)].mean()
               if len(m) > 1 else float("nan"))
    )

    return {
        "matrix":       corr_matrix,
        "rolling_mean": roll_corr,
        "window":       window,
    }