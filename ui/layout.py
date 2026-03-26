"""
ui/layout.py
Assembles the full Streamlit page layout.
Five tabs: Overview · Factors · Correlation · Risk (VaR) · Drawdown
"""

import streamlit as st
import ui.charts as charts


def render(ret, factors, regimes, corr, var_cvar, drawdown):
    st.title("Multi-Asset Risk Dashboard")
    st.caption("Indian equities · NSE · Historical simulation")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview",
        "⚖️ Factors",
        "🔗 Correlation",
        "📉 Risk (VaR)",
        "🌊 Drawdown",
    ])

    with tab1:
        st.subheader("Cumulative return · Volatility regime")
        fig = charts.cumulative_return_chart(ret, regimes)
        st.plotly_chart(fig, use_container_width=True)        

    with tab2:
        st.subheader("Factor exposure — Momentum · Value · Size")
        fig = charts.factor_bar_chart(factors)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(factors, use_container_width=True)

    with tab3:
        st.subheader(f"Rolling correlation ({corr['window']}-day window)")
        fig = charts.correlation_heatmap(corr["matrix"])
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("VaR 95%",  f"{var_cvar['var'][0.95]*100:.2f}%")
        c2.metric("CVaR 95%", f"{var_cvar['cvar'][0.95]*100:.2f}%")
        c3.metric("VaR 99%",  f"{var_cvar['var'][0.99]*100:.2f}%")
        c4.metric("CVaR 99%", f"{var_cvar['cvar'][0.99]*100:.2f}%")
        fig = charts.var_histogram(var_cvar)
        st.plotly_chart(fig, use_container_width=True)

    with tab5:
        c1, c2, c3 = st.columns(3)
        c1.metric("Max drawdown",  f"{drawdown['max_drawdown']*100:.2f}%")
        c2.metric("Avg drawdown",  f"{drawdown['avg_drawdown']*100:.2f}%")
        c3.metric("Recovery days",
                  str(drawdown["recovery_days"]) if drawdown["recovery_days"] else "Unrecovered")
        fig = charts.drawdown_chart(drawdown)
        st.plotly_chart(fig, use_container_width=True)
