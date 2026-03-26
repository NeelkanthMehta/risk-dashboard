# Multi-Asset Risk Dashboard

Interactive risk analytics dashboard for Indian equity portfolios (NSE).
Built with Python · Streamlit · Plotly.

**Live demo →** *(link after deploy)*

---

## Features

| Module | Method |
|---|---|
| Factor exposure | Momentum · Value · Size — cross-sectional z-scores |
| Volatility regime | 2-state Gaussian HMM on rolling realised vol |
| Rolling correlation | Pearson heatmap — configurable window (30/60/90/252d) |
| VaR & CVaR | Historical simulation — 95% & 99% confidence |
| Drawdown | Underwater equity curve · max DD · recovery days |

---

## Run locally

```bash
git clone https://github.com/NeelkanthMehta/risk-dashboard.git
cd risk-dashboard
uv sync
uv run streamlit run app.py
```

---

## Repo structure

```
risk-dashboard/
├── app.py                  # Streamlit entry point
├── requirements.txt
├── modules/
│   ├── portfolio.py        # yfinance data fetch
│   ├── returns.py          # log-returns + portfolio aggregation
│   ├── factors.py          # Momentum · Value · Size z-scores
│   ├── vol_regime.py       # HMM regime detection
│   ├── correlation.py      # Rolling correlation matrix
│   ├── var_cvar.py         # Historical simulation VaR/CVaR
│   └── drawdown.py         # Underwater curve + stats
└── ui/
    ├── sidebar.py          # Portfolio builder (tickers + weights)
    ├── charts.py           # Plotly figure factories
    └── layout.py           # Page layout + tabs
```

---

## Deployment

Hosted on [Streamlit Community Cloud](https://streamlit.io/cloud) — free tier.
Push to `main` → auto-deploys in ~60 seconds.

---

*By [Neelkanth Mehta](https://neelkanthmehta.vercel.app)*