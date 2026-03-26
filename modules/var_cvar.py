"""
var_cvar.py
Historical simulation Value-at-Risk and Conditional VaR (Expected Shortfall).
Uses the empirical return distribution — no parametric assumptions.
"""

import numpy as np
import pandas as pd


def compute_var_cvar(
    port_ret: pd.Series,
    confidence_levels: tuple[float, ...] = (0.95, 0.99),
    holding_period: int = 1,
) -> dict:
    """
    Parameters
    ----------
    port_ret          : daily portfolio log-return series
    confidence_levels : e.g. (0.95, 0.99)
    holding_period    : days (1 = daily VaR; scale by sqrt for multi-day)

    Returns
    -------
    dict with keys:
      'var'   — {conf_level: float}
      'cvar'  — {conf_level: float}
      'returns' — the full return series (for histogram)
      'hp_scale' — sqrt(holding_period) scaling factor applied
    """
    r = port_ret.dropna().values
    scale = np.sqrt(holding_period)

    var_results  = {}
    cvar_results = {}

    for cl in confidence_levels:
        cutoff = np.percentile(r, (1 - cl) * 100)
        var_results[cl]  = cutoff * scale
        cvar_results[cl] = r[r <= cutoff].mean() * scale

    return {
        "var":      var_results,
        "cvar":     cvar_results,
        "returns":  pd.Series(r, index=port_ret.dropna().index),
        "hp_scale": scale,
        "confidence_levels": confidence_levels,
    }
