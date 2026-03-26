"""
vol_regime.py
Fits a 2-state Gaussian Hidden Markov Model on realised volatility
to classify each trading day as Low or High vol regime.

Fixes vs v1:
- Rolling window reduced 21 → 5 days (preserves vol spikes)
- Uses both realised vol + absolute return as 2D feature (richer signal)
- 50 random restarts to avoid degenerate single-state solutions
"""

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
import streamlit as st


@st.cache_data(ttl=3600, show_spinner="Detecting volatility regimes…")
def detect_vol_regime(
    port_ret: pd.Series,
    n_states: int = 2,
    roll_window: int = 5,
    n_restarts: int = 50,
) -> pd.DataFrame:
    """
    Parameters
    ----------
    port_ret     : daily log-return series of the portfolio
    n_states     : number of HMM states (2 = Low / High)
    roll_window  : window for rolling realised vol feature
    n_restarts   : number of random initialisations (best log-likelihood kept)

    Returns
    -------
    pd.DataFrame — columns: ['return', 'realised_vol', 'state', 'regime_label']
    """
    realised_vol = port_ret.rolling(roll_window).std().dropna()
    abs_ret      = port_ret.abs().reindex(realised_vol.index).fillna(0)

    # 2D feature: [realised_vol, abs_return]
    feature = np.column_stack([realised_vol.values, abs_ret.values])

    best_model  = None
    best_score  = -np.inf

    for seed in range(n_restarts):
        try:
            model = GaussianHMM(
                n_components=n_states,
                covariance_type="full",
                n_iter=200,
                random_state=seed,
            )
            model.fit(feature)
            score = model.score(feature)
            if score > best_score:
                best_score = score
                best_model = model
        except Exception:
            continue

    if best_model is None:
        return pd.DataFrame()

    states = best_model.predict(feature)

    # Label by mean realised vol of each state
    state_means = {s: feature[states == s, 0].mean() for s in range(n_states)}
    sorted_states = sorted(state_means, key=state_means.get)
    labels = {sorted_states[0]: "Low", sorted_states[1]: "High"}

    result = pd.DataFrame(
        {
            "return":       port_ret.loc[realised_vol.index],
            "realised_vol": realised_vol,
            "state":        states,
            "regime_label": [labels[s] for s in states],
        }
    )
    return result