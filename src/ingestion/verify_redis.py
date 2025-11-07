"""Verify Redis connectivity and basic operations for Phase 1."""

import json
import logging
from datetime import datetime
from typing import Dict

from config.redis_config import get_redis_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_redis_connection() -> bool:
    """
    Test Redis connection and basic operations.

    Returns:
        True if all tests pass, False otherwise.
    """
    try:
        logger.info("Connecting to Redis...")
        r = get_redis_client()

        # Test 1: Ping
        ping_result = r.ping()
        if not ping_result:
            logger.error("Redis PING failed")
            return False
        logger.info("✓ Redis PING successful")

        # Test 2: Write a simple key-value
        test_key = "test:connection"
        test_value = "Phase1_verification"
        r.set(test_key, test_value)
        retrieved = r.get(test_key)

        if retrieved != test_value:
            logger.error(
                f"Write/Read mismatch: wrote '{test_value}', read '{retrieved}'")
            return False
        logger.info(
            f"✓ String write/read successful: {test_key} = {test_value}")

        # Test 3: Write with TTL (simulating cache behavior)
        ttl_key = "test:ttl"
        r.setex(ttl_key, 10, "expires_in_10_seconds")
        ttl = r.ttl(ttl_key)
        if ttl <= 0 or ttl > 10:
            logger.error(f"TTL test failed: expected 1-10 seconds, got {ttl}")
            return False
        logger.info(
            f"✓ TTL set successfully: {ttl_key} expires in {ttl} seconds")

        # Test 4: JSON data (simulating risk metric cache)
        metric_key = "VaR:TEST_PORT"
        metric_data: Dict = {
            "current_VaR_95": -0.0231,
            "ts": datetime.utcnow().isoformat() + "Z"
        }
        r.setex(metric_key, 60, json.dumps(metric_data))

        cached = r.get(metric_key)
        if not cached:
            logger.error("JSON cache write/read failed")
            return False

        retrieved_data = json.loads(cached)
        if retrieved_data["current_VaR_95"] != metric_data["current_VaR_95"]:
            logger.error("JSON data mismatch")
            return False
        logger.info(
            f"✓ JSON cache successful: {metric_key} stored with 60s TTL")

        # Test 5: Hash operations (simulating alert flags)
        alert_key = "Alert:TEST_PORT"
        r.hset(alert_key, "var_spike", "true")
        r.hset(alert_key, "beta_limit_breach", "false")
        r.expire(alert_key, 120)

        alert_data = r.hgetall(alert_key)
        if alert_data.get("var_spike") != "true":
            logger.error("Hash operation failed")
            return False
        logger.info(
            f"✓ Hash operations successful: {alert_key} set with 120s TTL")

        # Cleanup test keys
        r.delete(test_key, ttl_key, metric_key, alert_key)
        logger.info("✓ Cleanup successful: all test keys deleted")

        logger.info("\n" + "="*60)
        logger.info("Redis Verification: ALL TESTS PASSED")
        logger.info("="*60)
        return True

    except Exception as e:
        logger.error(f"Redis verification failed: {e}", exc_info=True)
        return False


def get_redis_info() -> None:
    """Display Redis server information."""
    try:
        r = get_redis_client()
        info = r.info()

        logger.info("\nRedis Server Information:")
        logger.info(f"  Version: {info.get('redis_version')}")
        logger.info(f"  Mode: {info.get('redis_mode')}")
        logger.info(f"  Memory Usage: {info.get('used_memory_human')}")
        logger.info(f"  Connected Clients: {info.get('connected_clients')}")
        logger.info(f"  Total Keys: {r.dbsize()}")
        logger.info(f"  Uptime (days): {info.get('uptime_in_days')}")

    except Exception as e:
        logger.error(f"Failed to get Redis info: {e}")


if __name__ == "__main__":
    success = verify_redis_connection()
    if success:
        get_redis_info()
        exit(0)
    else:
        logger.error("Redis verification failed. Check connection settings.")
        exit(1)
