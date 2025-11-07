"""
Portfolio Risk Analytics Dashboard

Real-time and historical risk metric visualization using MongoDB and Redis.
"""

import logging
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from alerts import evaluate_all_alerts, get_alert_color, get_threshold_info
from data_queries import (
    fetch_historical_metrics,
    fetch_latest_metrics,
    fetch_latest_portfolio_holdings,
    get_available_portfolios,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Portfolio Risk Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .alert-critical {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 10px;
        margin: 10px 0;
    }
    .alert-warning {
        background-color: #fff3e0;
        border-left: 5px solid #ff9800;
        padding: 10px;
        margin: 10px 0;
    }
    .data-source-badge {
        font-size: 12px;
        padding: 2px 8px;
        border-radius: 3px;
        margin-left: 10px;
    }
    .source-redis {
        background-color: #4caf50;
        color: white;
    }
    .source-mongodb {
        background-color: #2196f3;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_header():
    """Render dashboard header."""
    st.title("📊 Portfolio Risk Analytics Dashboard")
    st.markdown("**Real-time risk monitoring with MongoDB and Redis**")
    st.markdown("---")


def render_sidebar():
    """
    Render sidebar with portfolio selector and controls.

    Returns:
        Tuple of (selected_portfolio, days_back, refresh_button)
    """
    st.sidebar.header("⚙️ Dashboard Controls")

    # Get available portfolios
    portfolios = get_available_portfolios()

    if not portfolios:
        st.sidebar.error("No portfolios found in database")
        st.stop()

    # Portfolio selector
    selected_portfolio = st.sidebar.selectbox(
        "Select Portfolio",
        portfolios,
        help="Choose a portfolio to analyze",
    )

    # Date range picker
    days_back = st.sidebar.slider(
        "Historical Window (days)",
        min_value=7,
        max_value=365,
        value=60,
        step=7,
        help="Number of days to display in historical charts",
    )

    # Refresh button
    refresh = st.sidebar.button("🔄 Refresh Data", use_container_width=True)

    # Threshold information
    with st.sidebar.expander("📋 Alert Thresholds"):
        thresholds = get_threshold_info()
        st.write(f"**VaR Critical:** {thresholds['var_critical']:.2%}")
        st.write(f"**VaR Warning:** {thresholds['var_warning']:.2%}")
        st.write(f"**Beta High:** {thresholds['beta_high']:.2f}")
        st.write(f"**Beta Warning:** {thresholds['beta_warning']:.2f}")
        st.write(f"**Volatility High:** {thresholds['volatility_high']:.2%}")
        st.write(
            f"**Sharpe Negative Days:** {thresholds['sharpe_negative_days']}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Data Sources:**")
    st.sidebar.markdown("🔴 Redis - Real-time cache (60s TTL)")
    st.sidebar.markdown("🗄️ MongoDB - Historical persistent storage")

    return selected_portfolio, days_back, refresh


def render_alert_banner(alerts):
    """
    Display alert banner with active warnings.

    Args:
        alerts: List of alert dicts from evaluate_all_alerts()
    """
    if not alerts:
        st.success("✅ All metrics within healthy thresholds")
        return

    # Count by severity
    critical_count = sum(1 for a in alerts if a["severity"] == "critical")
    warning_count = sum(1 for a in alerts if a["severity"] == "warning")

    if critical_count > 0:
        st.error(f"🚨 {critical_count} Critical Alert(s)")
    elif warning_count > 0:
        st.warning(f"⚠️ {warning_count} Warning(s)")

    # Display individual alerts
    for alert in alerts:
        if alert["severity"] == "critical":
            st.markdown(
                f'<div class="alert-critical"><b>{alert["type"]}</b>: {alert["message"]}</div>',
                unsafe_allow_html=True,
            )
        elif alert["severity"] == "warning":
            st.markdown(
                f'<div class="alert-warning"><b>{alert["type"]}</b>: {alert["message"]}</div>',
                unsafe_allow_html=True,
            )


def render_metric_cards(metrics, data_source, latencies):
    """
    Display current metric values in cards.

    Args:
        metrics: Dict with metric values
        data_source: String indicating Redis or MongoDB
        latencies: Dict with query latencies
    """
    st.subheader("📈 Current Metrics")

    # Data source badge
    if "Redis" in data_source:
        badge_class = "source-redis"
        icon = "🔴"
    else:
        badge_class = "source-mongodb"
        icon = "🗄️"

    st.markdown(
        f'{icon} **Data Source:** <span class="data-source-badge {badge_class}">{data_source}</span>',
        unsafe_allow_html=True,
    )

    if metrics is None:
        st.error("No metric data available")
        return

    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        var_value = metrics.get("var", {}).get("value")
        if var_value is not None:
            st.metric(
                label="VaR (95%)",
                value=f"{var_value:.2%}",
                delta=None,
                help="Value at Risk - Potential loss at 95% confidence level",
            )
        else:
            st.metric(label="VaR (95%)", value="N/A")

    with col2:
        es_value = metrics.get("es", {}).get("value")
        if es_value is not None:
            st.metric(
                label="Expected Shortfall",
                value=f"{es_value:.2%}",
                delta=None,
                help="Average loss beyond VaR threshold",
            )
        else:
            st.metric(label="Expected Shortfall", value="N/A")

    with col3:
        sharpe_value = metrics.get("sharpe", {}).get("value")
        if sharpe_value is not None:
            delta_color = "normal" if sharpe_value >= 0 else "inverse"
            st.metric(
                label="Sharpe Ratio (20d)",
                value=f"{sharpe_value:.3f}",
                delta=None,
                help="Risk-adjusted return measure",
            )
        else:
            st.metric(label="Sharpe Ratio (20d)", value="N/A")

    with col4:
        beta_value = metrics.get("beta", {}).get("value")
        if beta_value is not None:
            st.metric(
                label="Beta vs SPY (20d)",
                value=f"{beta_value:.3f}",
                delta=None,
                help="Systematic risk relative to market",
            )
        else:
            st.metric(label="Beta vs SPY (20d)", value="N/A")

    # Display timestamp
    ts = metrics.get("var", {}).get("ts")
    if ts:
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            st.caption(f"Last updated: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        except:
            st.caption(f"Last updated: {ts}")


def render_historical_charts(df):
    """
    Render interactive Plotly charts for historical metrics.

    Args:
        df: DataFrame with historical metrics
    """
    if df is None or df.empty:
        st.warning("No historical data available for selected time range")
        return

    st.subheader("📉 Historical Trends")

    # Check which columns are available
    available_cols = set(df.columns)
    logger.info(f"Available columns for charting: {available_cols}")

    # Create two columns for charts
    col1, col2 = st.columns(2)

    with col1:
        # VaR time series
        if "VaR" in df.columns:
            fig_var = go.Figure()
            fig_var.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["VaR"],
                    mode="lines+markers",
                    name="VaR 95%",
                    line=dict(color="#f44336", width=2),
                    marker=dict(size=4),
                )
            )
            fig_var.update_layout(
                title="Value at Risk (95% Confidence)",
                xaxis_title="Date",
                yaxis_title="VaR (%)",
                hovermode="x unified",
                height=350,
            )
            fig_var.update_yaxes(tickformat=".2%")
            st.plotly_chart(fig_var, use_container_width=True)
        else:
            st.info("VaR data not available")

        # Sharpe ratio time series
        if "Sharpe" in df.columns:
            fig_sharpe = go.Figure()
            fig_sharpe.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["Sharpe"],
                    mode="lines+markers",
                    name="Sharpe Ratio",
                    line=dict(color="#2196f3", width=2),
                    marker=dict(size=4),
                )
            )
            # Add zero reference line
            fig_sharpe.add_hline(
                y=0, line_dash="dash", line_color="gray", annotation_text="Zero"
            )
            fig_sharpe.update_layout(
                title="Sharpe Ratio (20-day Rolling)",
                xaxis_title="Date",
                yaxis_title="Sharpe Ratio",
                hovermode="x unified",
                height=350,
            )
            st.plotly_chart(fig_sharpe, use_container_width=True)
        else:
            st.info("Sharpe Ratio data not available")

    with col2:
        # Beta time series
        if "Beta" in df.columns:
            fig_beta = go.Figure()
            fig_beta.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["Beta"],
                    mode="lines+markers",
                    name="Beta",
                    line=dict(color="#ff9800", width=2),
                    marker=dict(size=4),
                )
            )
            # Add 1.0 reference line (market beta)
            fig_beta.add_hline(
                y=1.0, line_dash="dash", line_color="gray", annotation_text="Market Beta"
            )
            fig_beta.update_layout(
                title="Beta vs SPY (20-day Rolling)",
                xaxis_title="Date",
                yaxis_title="Beta",
                hovermode="x unified",
                height=350,
            )
            st.plotly_chart(fig_beta, use_container_width=True)
        else:
            st.info("Beta data not available")

        # Volatility time series
        if "Volatility" in df.columns:
            fig_vol = go.Figure()
            fig_vol.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["Volatility"],
                    mode="lines+markers",
                    name="Volatility",
                    line=dict(color="#9c27b0", width=2),
                    marker=dict(size=4),
                )
            )
            fig_vol.update_layout(
                title="Portfolio Volatility (Annualized)",
                xaxis_title="Date",
                yaxis_title="Volatility (%)",
                hovermode="x unified",
                height=350,
            )
            fig_vol.update_yaxes(tickformat=".2%")
            st.plotly_chart(fig_vol, use_container_width=True)
        else:
            st.info("Volatility data not available")


def render_sector_exposure(holdings_data):
    """
    Render pie chart for sector exposure.

    Args:
        holdings_data: Dict with sector weights
    """
    st.subheader("🥧 Sector Exposure")

    if holdings_data is None:
        st.warning("No holdings data available")
        return

    sector_weights = holdings_data.get("sector_weights", {})

    if not sector_weights:
        st.warning("No sector breakdown available")
        return

    # Create DataFrame for plotting
    df_sectors = pd.DataFrame(
        list(sector_weights.items()), columns=["Sector", "Weight"]
    )
    df_sectors = df_sectors.sort_values("Weight", ascending=False)

    # Create pie chart
    fig_pie = px.pie(
        df_sectors,
        values="Weight",
        names="Sector",
        title="Current Sector Allocation",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    fig_pie.update_layout(height=400)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown("**Portfolio Summary:**")
        st.write(f"Total Assets: {holdings_data.get('num_assets', 'N/A')}")
        st.write(
            f"Gross Exposure: {holdings_data.get('gross_exposure', 'N/A'):.2f}")

        holdings_date = holdings_data.get("date")
        if holdings_date:
            st.write(f"As of: {holdings_date.strftime('%Y-%m-%d')}")


def render_performance_footer(latencies):
    """
    Display query performance metrics in footer.

    Args:
        latencies: Dict with query latencies
    """
    st.markdown("---")
    st.caption("**Performance Metrics:**")

    cols = st.columns(3)

    if "redis" in latencies:
        cols[0].caption(f"Redis Query: {latencies['redis']:.2f}ms")

    if "mongodb" in latencies:
        cols[1].caption(f"MongoDB Query: {latencies['mongodb']:.2f}ms")

    if "historical" in latencies:
        cols[2].caption(f"Historical Query: {latencies['historical']:.2f}ms")


def main():
    """Main dashboard application."""
    render_header()

    # Sidebar controls
    selected_portfolio, days_back, refresh = render_sidebar()

    # Clear cache if refresh clicked
    if refresh:
        st.cache_data.clear()
        st.rerun()

    # Fetch latest metrics
    with st.spinner("Loading metrics..."):
        metrics, data_source, latencies = fetch_latest_metrics(
            selected_portfolio)
        historical_df, hist_latency = fetch_historical_metrics(
            selected_portfolio, days_back
        )
        holdings_data, holdings_latency = fetch_latest_portfolio_holdings(
            selected_portfolio
        )

    # Add historical latency to dict
    latencies["historical"] = hist_latency

    # Evaluate alerts
    alerts = evaluate_all_alerts(metrics, historical_df)

    # Render components
    render_alert_banner(alerts)
    st.markdown("---")
    render_metric_cards(metrics, data_source, latencies)
    st.markdown("---")
    render_historical_charts(historical_df)
    st.markdown("---")
    render_sector_exposure(holdings_data)
    render_performance_footer(latencies)


if __name__ == "__main__":
    main()
