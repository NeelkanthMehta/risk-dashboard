"""
ui/sidebar.py
Renders the Streamlit sidebar for portfolio construction.
Exports: tickers, weights, lookback, corr_window
"""

import streamlit as st

# Defaults — representative NIFTY large-caps across sectors
_DEFAULT_TICKERS = [
    "RELIANCE.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "INFY.NS",
    "ICICIBANK.NS",
]
_DEFAULT_WEIGHTS = [0.25, 0.20, 0.20, 0.20, 0.15]

# Module-level exports (populated after render())
tickers    = []
weights    = {}
lookback   = 252
corr_window = 60


def render():
    global tickers, weights, lookback, corr_window

    with st.sidebar:
        st.markdown("## Portfolio")
        st.caption("Indian equities · NSE tickers (append `.NS`)")

        raw_input = st.text_area(
            "Tickers (one per line)",
            value="\n".join(_DEFAULT_TICKERS),
            height=140,
        )
        tickers = [t.strip().upper() for t in raw_input.splitlines() if t.strip()]

        st.markdown("#### Weights")
        weights = {}
        total = 0.0
        for i, t in enumerate(tickers):
            default_w = (
                _DEFAULT_WEIGHTS[i]
                if i < len(_DEFAULT_WEIGHTS)
                else round(1 / len(tickers), 2)
            )
            w = st.number_input(
                t, min_value=0.0, max_value=1.0,
                value=default_w, step=0.05, key=f"w_{t}"
            )
            weights[t] = w
            total += w

        if abs(total - 1.0) > 0.01:
            st.warning(f"Weights sum to {total:.2f} — will be normalised.")

        st.divider()
        st.markdown("## Settings")
        lookback = st.select_slider(
            "History (trading days)",
            options=[126, 252, 504, 756],
            value=252,
        )
        corr_window = st.select_slider(
            "Correlation window (days)",
            options=[30, 60, 90, 252],
            value=60,
        )

    return tickers, weights, lookback
