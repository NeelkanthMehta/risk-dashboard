"""
Multi-Asset Risk Dashboard
--------------------------
Streamlit app — entry point.
Run locally:  streamlit run app.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

st.set_page_config(
    page_title="Risk Dashboard · Neelkanth Mehta",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from modules.portfolio   import build_portfolio
from modules.returns     import compute_returns
from modules.factors     import compute_factor_exposure
from modules.vol_regime  import detect_vol_regime
from modules.correlation import rolling_correlation
from modules.var_cvar    import compute_var_cvar
from modules.drawdown    import compute_drawdown
import ui.sidebar   as sidebar
import ui.charts    as charts
import ui.layout    as layout

# ── Sidebar: portfolio construction ──────────────────────────────────────────
tickers, weights, lookback = sidebar.render()

# ── Data fetch + returns ──────────────────────────────────────────────────────
prices = build_portfolio(tickers, lookback)
st.write(f"Rows fetched: {len(prices)}, Tickers: {prices.columns.tolist()}")
st.write(prices.tail(3))
st.stop()

if prices.empty or len(prices) < 10:
    st.error("No price data returned for the selected tickers. Check that tickers use the '.NS' suffix (e.g. RELIANCE.NS) and try again.")
    st.stop()

ret = compute_returns(prices, weights)

# ── Analytics ────────────────────────────────────────────────────────────────
factors    = compute_factor_exposure(prices, weights)
regimes    = detect_vol_regime(ret["portfolio"])
corr       = rolling_correlation(ret["stocks"], window=sidebar.corr_window)
var_cvar   = compute_var_cvar(ret["portfolio"])
drawdown   = compute_drawdown(ret["portfolio"])

# ── Layout ────────────────────────────────────────────────────────────────────
layout.render(ret, factors, regimes, corr, var_cvar, drawdown)