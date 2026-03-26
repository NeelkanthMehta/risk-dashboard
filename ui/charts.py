"""
ui/charts.py
All Plotly figure factories. Each function returns a go.Figure.
Rendered via st.plotly_chart() in ui/layout.py.

Colour palette mirrors the portfolio site design system:
  Gold   #c9a84c  — primary accent
  Red    #e05c5c  — loss / risk / High-vol regime
  Green  #5cc98b  — gain / Low-vol regime
  Blue   #5b8dee  — neutral / informational
  Grey   #888ca0  — secondary / muted
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Design tokens ─────────────────────────────────────────────────────────────
GOLD  = "#c9a84c"
RED   = "#e05c5c"
GREEN = "#5cc98b"
BLUE  = "#5b8dee"
GREY  = "#888ca0"

PLOT_BG   = "#1a1f2e"
PAPER_BG  = "#1a1f2e"
GRID_COL  = "#2a3147"
TEXT_COL  = "#d0d4e8"
FONT_FMLY = "IBM Plex Mono, monospace"

_BASE_LAYOUT = dict(
    plot_bgcolor  = PLOT_BG,
    paper_bgcolor = PAPER_BG,
    font          = dict(family=FONT_FMLY, color=TEXT_COL, size=12),
    margin        = dict(l=60, r=30, t=50, b=50),
    xaxis=dict(gridcolor=GRID_COL, zeroline=False, showline=False),
    yaxis=dict(gridcolor=GRID_COL, zeroline=False, showline=False),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor=GRID_COL,
        font=dict(size=11),
    ),
    hoverlabel=dict(
        bgcolor="#252d42",
        bordercolor=GRID_COL,
        font_family=FONT_FMLY,
        font_size=12,
    ),
)


def _apply_base(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(title=dict(text=title, font=dict(size=14, color=GOLD)), **_BASE_LAYOUT)
    return fig


# ── 1. Cumulative return + regime shading ─────────────────────────────────────

def cumulative_return_chart(ret: dict, regimes: pd.DataFrame) -> go.Figure:
    """
    Cumulative portfolio return line with Low/High regime background bands.
    Secondary y-axis shows rolling realised volatility.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    cum = ret["cum_portfolio"] * 100          # in percent

    # ── Regime background bands (filled Scatter — more reliable than vrect) ──
    regime_colors = {
        "Low":  "rgba(92,201,139,0.12)",
        "High": "rgba(224,92,92,0.15)",
    }

    if not regimes.empty:
        label_col = regimes["regime_label"]
        dates     = regimes.index

        spans = []
        start = dates[0]
        prev  = label_col.iloc[0]
        for i in range(1, len(dates)):
            if label_col.iloc[i] != prev:
                spans.append((start, dates[i - 1], prev))
                start = dates[i]
                prev  = label_col.iloc[i]
        spans.append((start, dates[-1], prev))

        y_fill = 1e6   # large enough to cover any return value

        for x0, x1, label in spans:
            if x0 == x1:
                x1 = x1 + pd.Timedelta(days=1)
            color = regime_colors.get(label, "rgba(0,0,0,0)")
            fig.add_trace(
                go.Scatter(
                    x=[x0, x1, x1, x0, x0],
                    y=[-y_fill, -y_fill, y_fill, y_fill, -y_fill],
                    fill="toself",
                    fillcolor=color,
                    line=dict(width=0),
                    mode="lines",
                    showlegend=False,
                    hoverinfo="skip",
                    name=label,
                ),
                secondary_y=False,
            )

    # ── Cumulative return line ─────────────────────────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=cum.index, y=cum.values,
            name="Portfolio return",
            line=dict(color=GOLD, width=2),
            hovertemplate="%{x|%b %d %Y}<br>Return: <b>%{y:.2f}%</b><extra></extra>",
        ),
        secondary_y=False,
    )

    # ── Rolling realised vol (secondary axis) ─────────────────────────────────
    if not regimes.empty:
        rvol = regimes["realised_vol"] * 100
        fig.add_trace(
            go.Scatter(
                x=rvol.index, y=rvol.values,
                name="Realised vol (21d)",
                line=dict(color="#c8ccd8", width=2),
                opacity=0.6,
                hovertemplate="%{x|%b %d %Y}<br>Vol: <b>%{y:.2f}%</b><extra></extra>",
            ),
            secondary_y=True,
        )
        fig.update_yaxes(
            title_text="Realised vol (%)",
            secondary_y=True,
            gridcolor=GRID_COL,
            zeroline=False,
            showline=False,
            tickfont=dict(color=GREY, size=11),
        )

    # ── Zero line ─────────────────────────────────────────────────────────────
    fig.add_hline(y=0, line=dict(color=GREY, width=0.8, dash="dot"))

    # Regime legend entries (manual markers)
    for label, color in [("Low-vol regime", GREEN), ("High-vol regime", RED)]:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(color=color, size=10, symbol="square"),
            name=label, showlegend=True,
        ))

    fig.update_yaxes(
        title_text="Cumulative return (%)",
        secondary_y=False,
        ticksuffix="%",
        gridcolor=GRID_COL,
        zeroline=False,
    )

    _apply_base(fig, "Cumulative Return · Volatility Regime")
    fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.15))
    return fig


# ── 2. Factor exposure grouped bar ────────────────────────────────────────────

def factor_bar_chart(factors: pd.DataFrame) -> go.Figure:
    """
    Grouped horizontal bar chart of Momentum, Value, Size, Composite z-scores.
    Portfolio row is highlighted in gold; individual stocks in their factor colour.
    """
    df       = factors.copy()
    is_port  = df.index == "Portfolio"

    factor_colors = {
        "Momentum":  BLUE,
        "Value":     GREEN,
        "Size":      GREY,
        "Composite": GOLD,
    }

    fig = go.Figure()

    for factor, color in factor_colors.items():
        if factor not in df.columns:
            continue
        fig.add_trace(go.Bar(
            name=factor,
            y=df.index.tolist(),
            x=df[factor].tolist(),
            orientation="h",
            marker=dict(
                color=[GOLD if p else color for p in is_port],
                opacity=[1.0  if p else 0.75 for p in is_port],
                line=dict(width=0),
            ),
            hovertemplate="<b>%{y}</b><br>" + factor + ": <b>%{x:.2f}σ</b><extra></extra>",
        ))

    fig.add_vline(x=0, line=dict(color="#c8ccd8", width=2))

    _apply_base(fig, "Factor Exposure — Z-Scores")
    fig.update_layout(
        barmode="group",
        bargap=0.25,
        bargroupgap=0.05,
        xaxis_title="Z-score (σ)",
        yaxis=dict(autorange="reversed", gridcolor=GRID_COL),
        legend=dict(orientation="h", y=-0.15),
        height=max(300, len(df) * 55),
    )
    return fig


# ── 3. Rolling correlation heatmap ────────────────────────────────────────────

def correlation_heatmap(corr_matrix: pd.DataFrame) -> go.Figure:
    """
    Annotated Plotly heatmap. Diagonal is blanked out.
    """
    labels = corr_matrix.columns.tolist()
    n      = len(labels)
    z      = corr_matrix.values.copy().astype(float)

    for i in range(n):
        z[i, i] = np.nan

    text = [
        [f"{z[i][j]:.2f}" if not np.isnan(z[i][j]) else "" for j in range(n)]
        for i in range(n)
    ]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=labels,
        y=labels,
        text=text,
        texttemplate="%{text}",
        textfont=dict(size=11, family=FONT_FMLY),
        colorscale=[
            [0.0,  RED],
            [0.5,  "#252d42"],
            [1.0,  GREEN],
        ],
        zmid=0, zmin=-1, zmax=1,
        colorbar=dict(
            title="ρ",
            tickvals=[-1, -0.5, 0, 0.5, 1],
            tickfont=dict(size=11),
            thickness=12,
            len=0.8,
        ),
        hoverongaps=False,
        hovertemplate="<b>%{y} / %{x}</b><br>ρ = <b>%{z:.3f}</b><extra></extra>",
    ))

    _apply_base(fig, "Rolling Correlation Heatmap")
    fig.update_layout(
        xaxis=dict(side="bottom", tickangle=-30, gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(autorange="reversed",          gridcolor="rgba(0,0,0,0)"),
        height=max(350, n * 60 + 100),
    )
    return fig


# ── 4. VaR / CVaR histogram ───────────────────────────────────────────────────

def var_histogram(var_cvar: dict) -> go.Figure:
    """
    Return distribution histogram with tail shading and VaR/CVaR vertical lines.
    """
    returns = var_cvar["returns"] * 100
    var     = {cl: v * 100 for cl, v in var_cvar["var"].items()}
    cvar    = {cl: v * 100 for cl, v in var_cvar["cvar"].items()}

    fig = go.Figure()

    # Full distribution
    fig.add_trace(go.Histogram(
        x=returns, nbinsx=80,
        name="Daily returns",
        marker=dict(color=BLUE, opacity=0.55, line=dict(width=0)),
        hovertemplate="Return: <b>%{x:.2f}%</b><br>Count: <b>%{y}</b><extra></extra>",
    ))

    # Tail fills
    for cl, color, opacity, name in [
        (0.95, RED,     0.45, "95% tail"),
        (0.99, "#b03030", 0.6, "99% tail"),
    ]:
        tail = returns[returns <= var[cl]]
        fig.add_trace(go.Histogram(
            x=tail, nbinsx=80,
            name=name,
            marker=dict(color=color, opacity=opacity, line=dict(width=0)),
            hoverinfo="skip",
        ))

    # Vertical threshold lines
    line_specs = [
        (var[0.95],  "VaR 95%",  GOLD, "dash"),
        (cvar[0.95], "CVaR 95%", GOLD, "dot"),
        (var[0.99],  "VaR 99%",  RED,  "dash"),
        (cvar[0.99], "CVaR 99%", RED,  "dot"),
    ]
    for xval, label, color, dash in line_specs:
        fig.add_vline(
            x=xval,
            line=dict(color=color, width=1.5, dash=dash),
            annotation_text=f" {label}: {xval:.2f}%",
            annotation_position="top right",
            annotation_font=dict(size=10, color=color, family=FONT_FMLY),
        )

    _apply_base(fig, "Return Distribution — VaR & CVaR")
    fig.update_layout(
        barmode="overlay",
        xaxis_title="Daily return (%)",
        yaxis_title="Frequency",
        xaxis_ticksuffix="%",
        legend=dict(orientation="h", y=-0.15),
    )
    return fig


# ── 5. Drawdown underwater chart ──────────────────────────────────────────────

def drawdown_chart(drawdown: dict) -> go.Figure:
    """
    Two-panel chart: cumulative return (top) + underwater drawdown curve (bottom).
    Max drawdown annotated; drawdown period shaded.
    """
    dd  = drawdown["drawdown"]  * 100
    cum = drawdown["cum_return"] * 100

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.45, 0.55],
        vertical_spacing=0.06,
    )

    # Top: cumulative return
    fig.add_trace(
        go.Scatter(
            x=cum.index, y=cum.values,
            name="Cumulative return",
            line=dict(color=GOLD, width=1.8),
            fill="tozeroy",
            fillcolor="rgba(201,168,76,0.10)",
            hovertemplate="%{x|%b %d %Y}<br>Return: <b>%{y:.2f}%</b><extra></extra>",
        ),
        row=1, col=1,
    )

    # Bottom: underwater curve
    fig.add_trace(
        go.Scatter(
            x=dd.index, y=dd.values,
            name="Drawdown",
            line=dict(color=RED, width=1.5),
            fill="tozeroy",
            fillcolor="rgba(224,92,92,0.18)",
            hovertemplate="%{x|%b %d %Y}<br>Drawdown: <b>%{y:.2f}%</b><extra></extra>",
        ),
        row=2, col=1,
    )

    # Max drawdown annotation
    max_dd  = drawdown["max_drawdown"] * 100
    trough  = drawdown["max_dd_trough"]
    peak    = drawdown["max_dd_start"]

    fig.add_annotation(
        x=str(trough), y=max_dd,
        text=f"Max DD: {max_dd:.2f}%",
        showarrow=True,
        arrowhead=2, arrowcolor=RED, arrowwidth=1.5,
        ax=60, ay=-30,
        font=dict(color=RED, size=11, family=FONT_FMLY),
        row=2, col=1,
    )

    # Drawdown period shading
    recovery = drawdown.get("max_dd_end")
    if recovery:
        fig.add_vrect(
            x0=str(peak), x1=str(recovery),
            fillcolor="rgba(224,92,92,0.07)",
            layer="below", line_width=0,
        )

    _apply_base(fig, "Drawdown Analysis")
    fig.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.10),
    )
    for row in [1, 2]:
        fig.update_yaxes(
            ticksuffix="%", gridcolor=GRID_COL,
            zeroline=True, zerolinecolor=GREY, zerolinewidth=0.8,
            showline=False, row=row, col=1,
        )
        fig.update_xaxes(
            gridcolor=GRID_COL, zeroline=False, showline=False,
            row=row, col=1,
        )
    fig.update_yaxes(title_text="Return (%)",   row=1, col=1)
    fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)

    return fig