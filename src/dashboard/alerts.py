"""
Alert logic for portfolio risk monitoring.

Checks risk metrics against configurable thresholds and generates
visual alerts for the dashboard.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# Configurable alert thresholds
THRESHOLDS = {
    "var_critical": -0.02,  # VaR worse than -2%
    "var_warning": -0.015,  # VaR worse than -1.5%
    "beta_high": 1.5,  # Beta exceeds 1.5
    "beta_warning": 1.3,  # Beta exceeds 1.3
    "sharpe_negative_days": 10,  # Negative Sharpe for > 10 days
    "volatility_high": 0.30,  # Annualized volatility > 30%
}

# Add trend/spike thresholds without changing the original dict
THRESHOLDS.update({
    # VaR spike: day-over-day worsening (by absolute magnitude)
    "var_spike_critical_pct": 0.20,  # ≥ +20% worse vs yesterday
    "var_spike_warning_pct": 0.10,   # ≥ +10% worse vs yesterday

    # Beta rising trend over the last N days (least-squares slope)
    "beta_trend_days": 5,
    "beta_trend_min_slope": 0.02,    # per-day slope considered "rising fast"
})


def check_var_threshold(var_value: Optional[float]) -> Tuple[str, str, str]:
    """
    Check if VaR exceeds risk thresholds.

    Args:
        var_value: Current VaR value (negative percentage)

    Returns:
        Tuple of (severity level, alert type, message)
        Severity: "critical", "warning", "healthy", or "none"
    """
    if var_value is None:
        return "none", "", ""

    if var_value < THRESHOLDS["var_critical"]:
        return (
            "critical",
            "VaR Critical",
            f"VaR at {var_value:.2%} exceeds critical threshold ({THRESHOLDS['var_critical']:.2%})"
        )
    elif var_value < THRESHOLDS["var_warning"]:
        return (
            "warning",
            "VaR Elevated",
            f"VaR at {var_value:.2%} exceeds warning threshold ({THRESHOLDS['var_warning']:.2%})"
        )
    else:
        return "healthy", "", ""


def check_beta_threshold(beta_value: Optional[float]) -> Tuple[str, str, str]:
    """
    Check if Beta exceeds risk thresholds.

    Args:
        beta_value: Current Beta vs benchmark

    Returns:
        Tuple of (severity level, alert type, message)
    """
    if beta_value is None:
        return "none", "", ""

    if beta_value > THRESHOLDS["beta_high"]:
        return (
            "critical",
            "High Beta",
            f"Beta at {beta_value:.2f} exceeds high threshold ({THRESHOLDS['beta_high']:.2f})"
        )
    elif beta_value > THRESHOLDS["beta_warning"]:
        return (
            "warning",
            "Elevated Beta",
            f"Beta at {beta_value:.2f} exceeds warning threshold ({THRESHOLDS['beta_warning']:.2f})"
        )
    else:
        return "healthy", "", ""


def check_volatility_threshold(vol_value: Optional[float]) -> Tuple[str, str, str]:
    """
    Check if portfolio volatility exceeds threshold.

    Args:
        vol_value: Annualized portfolio volatility

    Returns:
        Tuple of (severity level, alert type, message)
    """
    if vol_value is None:
        return "none", "", ""

    if vol_value > THRESHOLDS["volatility_high"]:
        return (
            "warning",
            "High Volatility",
            f"Portfolio volatility at {vol_value:.2%} exceeds threshold ({THRESHOLDS['volatility_high']:.2%})"
        )
    else:
        return "healthy", "", ""


def check_sharpe_persistence(historical_df: Optional[pd.DataFrame]) -> Tuple[str, str, str]:
    """
    Check if Sharpe ratio has been negative for extended period.

    Args:
        historical_df: DataFrame with date and Sharpe columns

    Returns:
        Tuple of (severity level, alert type, message)
    """
    if historical_df is None or historical_df.empty or "Sharpe" not in historical_df.columns:
        return "none", "", ""

    try:
        # Get most recent data (last N days)
        df_recent = historical_df.tail(THRESHOLDS["sharpe_negative_days"])

        if len(df_recent) < THRESHOLDS["sharpe_negative_days"]:
            # Not enough data to assess persistence
            return "none", "", ""

        # Count negative Sharpe days
        negative_days = (df_recent["Sharpe"] < 0).sum()

        if negative_days >= THRESHOLDS["sharpe_negative_days"]:
            return (
                "warning",
                "Persistent Negative Sharpe",
                f"Sharpe ratio negative for {negative_days} of last {THRESHOLDS['sharpe_negative_days']} days"
            )
        # 70% threshold
        elif negative_days >= THRESHOLDS["sharpe_negative_days"] * 0.7:
            return (
                "warning",
                "Declining Sharpe",
                f"Sharpe ratio negative for {negative_days} of last {THRESHOLDS['sharpe_negative_days']} days"
            )
        else:
            return "healthy", "", ""

    except Exception as e:
        logger.error(f"Error checking Sharpe persistence: {e}")
        return "none", "", ""

def check_var_spike(historical_df: Optional[pd.DataFrame]) -> Tuple[str, str, str]:
    """
    Detect day-over-day VaR 'spikes' based on absolute magnitude change.
    Expects a column named 'VaR' (case-insensitive accepted).
    Returns (severity, type, message).
    """
    if historical_df is None or historical_df.empty:
        return "none", "", ""

    # Be flexible about column name casing
    col_candidates = [c for c in historical_df.columns if c.lower() == "var"]
    if not col_candidates:
        return "none", "", ""
    col = col_candidates[0]

    try:
        series = historical_df[col].dropna()
        if len(series) < 2:
            return "none", "", ""

        prev, curr = float(series.iloc[-2]), float(series.iloc[-1])
        # Compare by magnitude (both typically negative)
        prev_mag, curr_mag = abs(prev), abs(curr)
        if prev_mag == 0:
            return "none", "", ""

        change_pct = (curr_mag - prev_mag) / prev_mag  # e.g., +0.25 = 25% worse
        crit = THRESHOLDS["var_spike_critical_pct"]
        warn = THRESHOLDS["var_spike_warning_pct"]

        if change_pct >= crit:
            return (
                "critical",
                "VaR Spike",
                f"VaR worsened by {change_pct:.0%} day-over-day "
                f"({curr:.2%} vs {prev:.2%})"
            )
        elif change_pct >= warn:
            return (
                "warning",
                "VaR Rising",
                f"VaR worsened by {change_pct:.0%} day-over-day "
                f"({curr:.2%} vs {prev:.2%})"
            )
        else:
            return "healthy", "", ""
    except Exception as e:
        logger.error(f"Error checking VaR spike: {e}")
        return "none", "", ""


def check_beta_trend(historical_df: Optional[pd.DataFrame], latest_beta: Optional[float]) -> Tuple[str, str, str]:
    """
    Flag 'rising beta' when (a) latest beta is already elevated, and
    (b) the short-term slope over the last N days is positive and large enough.
    Expects a column named 'Beta' (case-insensitive accepted).
    Returns (severity, type, message).
    """
    if historical_df is None or historical_df.empty or latest_beta is None:
        return "none", "", ""

    col_candidates = [c for c in historical_df.columns if c.lower() == "beta"]
    if not col_candidates:
        return "none", "", ""
    col = col_candidates[0]

    try:
        beta_series = historical_df[col].dropna()
        n = THRESHOLDS["beta_trend_days"]
        if len(beta_series) < n:
            return "none", "", ""

        # Least-squares slope over last n points
        y = beta_series.iloc[-n:].to_numpy(dtype=float)
        x = np.arange(len(y))
        slope = np.polyfit(x, y, 1)[0]  # per-day slope

        # Only care if latest beta is already above warning threshold
        if latest_beta > THRESHOLDS["beta_warning"] and slope >= THRESHOLDS["beta_trend_min_slope"]:
            # Escalate to critical if also above high threshold
            sev = "critical" if latest_beta > THRESHOLDS["beta_high"] else "warning"
            return (
                sev,
                "Rising Beta",
                f"Beta rising (slope≈{slope:.3f}/day), latest {latest_beta:.2f} "
                f"(warn ≥ {THRESHOLDS['beta_warning']:.2f}, high ≥ {THRESHOLDS['beta_high']:.2f})"
            )
        return "healthy", "", ""
    except Exception as e:
        logger.error(f"Error checking Beta trend: {e}")
        return "none", "", ""



def evaluate_all_alerts(
    latest_metrics: Optional[Dict],
    historical_df: Optional[pd.DataFrame]
) -> List[Dict[str, str]]:
    """
    Evaluate all alert conditions and return list of active alerts.

    Args:
        latest_metrics: Dict with current metric values (var, beta, sharpe, etc.)
        historical_df: DataFrame with historical metrics for persistence checks

    Returns:
        List of alert dicts with keys: severity, type, message
        Sorted by severity (critical first)
    """
    alerts = []

    if latest_metrics is None:
        return alerts

    # Extract current values
    var_value = latest_metrics.get("var", {}).get("value")
    beta_value = latest_metrics.get("beta", {}).get("value")
    vol_value = latest_metrics.get("volatility", {}).get("value")

    # Check VaR threshold
    severity, alert_type, message = check_var_threshold(var_value)
    if severity in ["critical", "warning"]:
        alerts.append({
            "severity": severity,
            "type": alert_type,
            "message": message
        })

    # Check Beta threshold
    severity, alert_type, message = check_beta_threshold(beta_value)
    if severity in ["critical", "warning"]:
        alerts.append({
            "severity": severity,
            "type": alert_type,
            "message": message
        })

    # Check Volatility threshold
    severity, alert_type, message = check_volatility_threshold(vol_value)
    if severity in ["critical", "warning"]:
        alerts.append({
            "severity": severity,
            "type": alert_type,
            "message": message
        })

    # Check Sharpe persistence
    severity, alert_type, message = check_sharpe_persistence(historical_df)
    if severity in ["critical", "warning"]:
        alerts.append({
            "severity": severity,
            "type": alert_type,
            "message": message
        })

    # Check VaR day-over-day spike (trend-sensitive)
    severity, alert_type, message = check_var_spike(historical_df)
    if severity in ["critical", "warning"]:
        alerts.append({
            "severity": severity,
            "type": alert_type,
            "message": message
        })

    # Check Beta rising trend (uses short-term slope)
    severity, alert_type, message = check_beta_trend(historical_df, beta_value)
    if severity in ["critical", "warning"]:
        alerts.append({
            "severity": severity,
            "type": alert_type,
            "message": message
        })

    # Sort by severity (critical first)
    severity_order = {"critical": 0, "warning": 1}
    alerts.sort(key=lambda x: severity_order.get(x["severity"], 2))

    logger.info(f"Alert evaluation complete: {len(alerts)} active alerts")
    return alerts


def get_alert_color(severity: str) -> str:
    """
    Get color code for alert severity level.

    Args:
        severity: Alert severity ("critical", "warning", "healthy")

    Returns:
        Color name for Streamlit styling
    """
    color_map = {
        "critical": "red",
        "warning": "orange",
        "healthy": "green",
        "none": "gray"
    }
    return color_map.get(severity, "gray")

def get_threshold_info() -> Dict[str, any]:
    """
    Get current threshold configuration for display.

    Returns:
        Dict of threshold names and values
    """
    return THRESHOLDS.copy()
