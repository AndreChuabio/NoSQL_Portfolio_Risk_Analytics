"""Redis cache manager for real-time risk metrics."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from config.redis_config import get_redis_client

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages Redis cache for portfolio risk metrics."""

    def __init__(self, default_ttl: int = 60):
        """
        Initialize cache manager.

        Args:
            default_ttl: Default time-to-live in seconds (default 60)
        """
        self.redis_client = get_redis_client()
        self.default_ttl = default_ttl
        logger.info(f"CacheManager initialized with TTL={default_ttl}s")

    def _build_key(self, metric_type: str, portfolio_id: str) -> str:
        """
        Build Redis key following naming convention.

        Format: <metric_type>:<portfolio_id>

        Args:
            metric_type: Type of metric (VaR, Sharpe, Beta, Alert, etc.)
            portfolio_id: Portfolio identifier

        Returns:
            Formatted Redis key string

        Example:
            >>> cm = CacheManager()
            >>> key = cm._build_key("VaR", "PORT_A_TechGrowth")
            >>> print(key)
            VaR:PORT_A_TechGrowth
        """
        return f"{metric_type}:{portfolio_id}"

    def set_metric(
        self,
        portfolio_id: str,
        metric_type: str,
        value: float,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Store a risk metric in Redis cache with TTL.

        Args:
            portfolio_id: Portfolio identifier
            metric_type: Type of metric (VaR, Sharpe, Beta)
            value: Metric value to cache
            ttl: Time-to-live in seconds (uses default if None)
            metadata: Optional additional data to store

        Returns:
            True if successfully cached, False otherwise

        Example:
            >>> cm = CacheManager()
            >>> cm.set_metric("PORT_A_TechGrowth", "VaR", -0.0231, metadata={"confidence": 0.95})
        """
        key = self._build_key(metric_type, portfolio_id)
        ttl_seconds = ttl if ttl is not None else self.default_ttl

        data = {
            f"current_{metric_type}": value,
            "ts": datetime.now(timezone.utc).isoformat(),
        }

        if metadata:
            data.update(metadata)

        try:
            self.redis_client.setex(name=key, time=ttl_seconds, value=json.dumps(data))
            logger.info(
                f"Cached {metric_type} for {portfolio_id}: {value:.6f} (TTL={ttl_seconds}s)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to cache {metric_type} for {portfolio_id}: {e}", exc_info=True)
            return False

    def get_metric(
        self, portfolio_id: str, metric_type: str, max_age_seconds: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached risk metric from Redis.

        Args:
            portfolio_id: Portfolio identifier
            metric_type: Type of metric (VaR, Sharpe, Beta)
            max_age_seconds: Maximum acceptable age of cached data (optional)

        Returns:
            Dictionary with metric value and metadata, or None if not found/expired

        Example:
            >>> cm = CacheManager()
            >>> data = cm.get_metric("PORT_A_TechGrowth", "VaR", max_age_seconds=120)
            >>> if data:
            ...     print(f"VaR: {data['current_VaR']}, cached at {data['ts']}")
        """
        key = self._build_key(metric_type, portfolio_id)

        try:
            cached = self.redis_client.get(key)

            if cached is None:
                logger.debug(f"Cache miss for {key}")
                return None

            data = json.loads(cached)

            if max_age_seconds is not None and "ts" in data:
                cached_time = datetime.fromisoformat(data["ts"].replace("Z", "+00:00"))
                age_seconds = (datetime.now(timezone.utc) - cached_time).total_seconds()

                if age_seconds > max_age_seconds:
                    logger.warning(
                        f"Cached data for {key} is stale: {age_seconds:.1f}s > {max_age_seconds}s"
                    )
                    return None

            logger.debug(f"Cache hit for {key}")
            return data

        except Exception as e:
            logger.error(f"Failed to retrieve {metric_type} for {portfolio_id}: {e}", exc_info=True)
            return None

    def set_all_metrics(
        self,
        portfolio_id: str,
        var_95: float,
        expected_shortfall: float,
        sharpe_ratio: float,
        beta: float,
        volatility: float,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Store all risk metrics for a portfolio in a single operation.

        Args:
            portfolio_id: Portfolio identifier
            var_95: 95% Value-at-Risk
            expected_shortfall: Expected Shortfall
            sharpe_ratio: Sharpe ratio
            beta: Beta vs benchmark
            volatility: Portfolio volatility
            ttl: Time-to-live in seconds (uses default if None)

        Returns:
            True if all metrics successfully cached, False otherwise
        """
        ttl_seconds = ttl if ttl is not None else self.default_ttl

        metrics = {
            "VaR_95": var_95,
            "ES": expected_shortfall,
            "Sharpe": sharpe_ratio,
            "Beta": beta,
            "Volatility": volatility,
        }

        try:
            pipeline = self.redis_client.pipeline()

            for metric_type, value in metrics.items():
                key = self._build_key(metric_type, portfolio_id)
                data = {
                    f"current_{metric_type}": value,
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
                pipeline.setex(name=key, time=ttl_seconds, value=json.dumps(data))

            pipeline.execute()

            logger.info(
                f"Cached all metrics for {portfolio_id}: "
                f"VaR={var_95:.6f}, ES={expected_shortfall:.6f}, "
                f"Sharpe={sharpe_ratio:.4f}, Beta={beta:.4f}, Vol={volatility:.6f}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to cache all metrics for {portfolio_id}: {e}", exc_info=True)
            return False

    def set_alert(
        self,
        portfolio_id: str,
        alert_name: str,
        is_triggered: bool,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set an alert flag in Redis cache.

        Args:
            portfolio_id: Portfolio identifier
            alert_name: Name of alert (e.g., 'var_spike', 'beta_limit_breach')
            is_triggered: Whether alert is currently triggered
            ttl: Time-to-live in seconds (uses default if None)

        Returns:
            True if successfully cached, False otherwise

        Example:
            >>> cm = CacheManager()
            >>> cm.set_alert("PORT_A_TechGrowth", "var_spike", True, ttl=120)
        """
        key = self._build_key("Alert", portfolio_id)
        ttl_seconds = ttl if ttl is not None else self.default_ttl

        try:
            self.redis_client.hset(key, alert_name, str(is_triggered).lower())
            self.redis_client.expire(key, ttl_seconds)

            logger.info(
                f"Alert '{alert_name}' for {portfolio_id}: {is_triggered} (TTL={ttl_seconds}s)"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to set alert '{alert_name}' for {portfolio_id}: {e}", exc_info=True
            )
            return False

    def get_all_alerts(self, portfolio_id: str) -> Optional[Dict[str, bool]]:
        """
        Retrieve all alert flags for a portfolio.

        Args:
            portfolio_id: Portfolio identifier

        Returns:
            Dictionary mapping alert names to boolean status, or None if not found

        Example:
            >>> cm = CacheManager()
            >>> alerts = cm.get_all_alerts("PORT_A_TechGrowth")
            >>> if alerts and alerts.get("var_spike"):
            ...     print("VaR spike alert is active!")
        """
        key = self._build_key("Alert", portfolio_id)

        try:
            alerts = self.redis_client.hgetall(key)

            if not alerts:
                logger.debug(f"No alerts found for {portfolio_id}")
                return None

            parsed_alerts = {
                k.decode("utf-8") if isinstance(k, bytes) else k: (
                    v.decode("utf-8").lower() == "true"
                    if isinstance(v, bytes)
                    else str(v).lower() == "true"
                )
                for k, v in alerts.items()
            }

            logger.debug(f"Retrieved {len(parsed_alerts)} alerts for {portfolio_id}")
            return parsed_alerts

        except Exception as e:
            logger.error(f"Failed to retrieve alerts for {portfolio_id}: {e}", exc_info=True)
            return None

    def clear_portfolio_cache(self, portfolio_id: str) -> int:
        """
        Clear all cached metrics for a portfolio.

        Args:
            portfolio_id: Portfolio identifier

        Returns:
            Number of keys deleted

        Example:
            >>> cm = CacheManager()
            >>> deleted = cm.clear_portfolio_cache("PORT_A_TechGrowth")
            >>> print(f"Cleared {deleted} cached keys")
        """
        metric_types = ["VaR_95", "ES", "Sharpe", "Beta", "Volatility", "Alert"]
        keys_to_delete = [self._build_key(mt, portfolio_id) for mt in metric_types]

        try:
            deleted = self.redis_client.delete(*keys_to_delete)
            logger.info(f"Cleared {deleted} cached keys for {portfolio_id}")
            return deleted

        except Exception as e:
            logger.error(f"Failed to clear cache for {portfolio_id}: {e}", exc_info=True)
            return 0

    def health_check(self) -> bool:
        """
        Verify Redis connection health.

        Returns:
            True if Redis is responsive, False otherwise
        """
        try:
            response = self.redis_client.ping()
            if response:
                logger.info("Redis health check: OK")
                return True
            else:
                logger.error("Redis health check: FAILED (no PONG response)")
                return False

        except Exception as e:
            logger.error(f"Redis health check: FAILED ({e})", exc_info=True)
            return False
