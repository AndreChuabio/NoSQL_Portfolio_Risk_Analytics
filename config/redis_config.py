"""Redis connection utilities for the NoSQL portfolio risk analytics project."""

from redis import Redis


def get_redis_client(host: str = "localhost", port: int = 6379, db: int = 0, password: str | None = None) -> Redis:
    """Return a configured Redis client.

    Args:
        host: Redis host name.
        port: Redis TCP port.
        db: Redis database index.
        password: Optional password for authenticated deployments.

    Returns:
        Redis client instance.
    """
    return Redis(host=host, port=port, db=db, password=password, decode_responses=True)
