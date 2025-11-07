"""MongoDB connection utilities for the NoSQL portfolio risk analytics project."""

import os
from typing import Dict, Optional

from pymongo import MongoClient


def get_mongo_client(uri: Optional[str] = None) -> MongoClient:
    """Create a MongoDB client using the provided URI or the default local connection.

    Args:
        uri: Optional connection string. Defaults to MongoDB instance exposed by docker-compose.

    Returns:
        A configured MongoClient instance.
    """
    connection_uri = uri or os.getenv(
        "MONGODB_URI", "mongodb://root:example@localhost:27017/?authSource=admin"
    )
    return MongoClient(connection_uri)


def get_database(client: MongoClient, db_name: str = "portfolio_risk") -> Dict[str, object]:
    """Return a handle to the configured MongoDB database.

    Args:
        client: An active MongoClient instance.
        db_name: Name of the target database.

    Returns:
        MongoDB database handle.
    """
    return client[db_name]
