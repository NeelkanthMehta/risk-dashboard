"""
drawdown.py
Computes the underwater equity curve and key drawdown statistics.
"""

import numpy as np
import pandas as pd


def compute_drawdown(port_ret: pd.Series) -> dict:
    """
    Parameters
    ----------
    port_ret : daily log-return series

    Returns
    -------
    dict with keys:
      'drawdown'       — pd.Series of drawdown depth at each date (negative %)
      'cum_return'     — pd.Series of cumulative return
      'max_drawdown'   — float (most negative value)
      'avg_drawdown'   — float (mean of all drawdown values < 0)
      'max_dd_start'   — date
      'max_dd_trough'  — date
      'max_dd_end'     — date  (first recovery date, or None if unrecovered)
      'recovery_days'  — int or None
    """
    cum = port_ret.cumsum().apply(np.exp)          # wealth index
    rolling_max = cum.cummax()
    drawdown = (cum / rolling_max) - 1             # 0 at new highs, negative in drawdown

    max_dd = drawdown.min()
    trough_idx = drawdown.idxmin()
    peak_idx   = rolling_max.loc[:trough_idx].idxmax()

    # Recovery: first date after trough where drawdown returns to 0
    post_trough = drawdown.loc[trough_idx:]
    recovered   = post_trough[post_trough >= 0]
    recovery_date   = recovered.index[0] if len(recovered) > 0 else None
    recovery_days   = (recovery_date - trough_idx).days if recovery_date else None

    return {
        "drawdown":      drawdown,
        "cum_return":    cum - 1,
        "max_drawdown":  round(max_dd, 4),
        "avg_drawdown":  round(drawdown[drawdown < 0].mean(), 4),
        "max_dd_start":  peak_idx,
        "max_dd_trough": trough_idx,
        "max_dd_end":    recovery_date,
        "recovery_days": recovery_days,
    }
