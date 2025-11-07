"""Redis connection utilities for the NoSQL portfolio risk analytics project."""

import os
from typing import Optional
from redis import Redis


def get_redis_client(
    host: Optional[str] = None,
    port: Optional[int] = None,
    db: int = 0,
    password: Optional[str] = None
) -> Redis:
    """Return a configured Redis client.

    Supports both local and cloud Redis deployments. Connection parameters are
    read from environment variables if not explicitly provided.

    Args:
        host: Redis host name. Defaults to REDIS_HOST env var or "localhost".
        port: Redis TCP port. Defaults to REDIS_PORT env var or 6379.
        db: Redis database index (0-15).
        password: Optional password. Defaults to REDIS_PASSWORD env var.

    Returns:
        Redis client instance with decode_responses=True.

    Environment Variables:
        REDIS_HOST: Redis server hostname (e.g., redis-12345.c123.redns.redis-cloud.com)
        REDIS_PORT: Redis server port (default: 6379)
        REDIS_PASSWORD: Authentication password for cloud Redis

    Examples:
        # Local Redis (no auth)
        >>> client = get_redis_client()

        # Redis Cloud (reads from env vars)
        >>> client = get_redis_client()

        # Explicit connection
        >>> client = get_redis_client(host="my-redis.cloud.com", port=12345, password="secret")
    """
    redis_host = host or os.getenv("REDIS_HOST", "localhost")
    redis_port = port or int(os.getenv("REDIS_PORT", "6379"))
    redis_password = password or os.getenv("REDIS_PASSWORD")

    return Redis(
        host=redis_host,
        port=redis_port,
        db=db,
        password=redis_password,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
