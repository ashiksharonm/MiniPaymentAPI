"""
Redis Client Manager.

Handles caching and idempotency mechanisms to allow scaling 
the Mini Payments API gracefully under heavy load.
"""
import json
import logging
from typing import Optional, Any
import redis
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

# IDEMPOTENCY_TTL controls how long we keep a key in memory.
# In a real bank, this might be 24-48 hours. Let's use 24h (86400 seconds)
IDEMPOTENCY_TTL = 86400 

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Singleton pattern to return a connected redis client or dummy fallback."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=2.0  # Fail fast if Redis is down
            )
            # Test connection
            _redis_client.ping()
            logger.info("Successfully connected to Redis cache.")
        except redis.ConnectionError as e:
            logger.warning(f"Could not connect to Redis: {e}. Falling back to DB-only.")
            _redis_client = None  # We will handle None gracefully in the service
    return _redis_client


def get_idempotent_transaction(idempotency_key: str) -> Optional[dict]:
    """
    Look up a transaction dict from Redis by idempotency_key in O(1) time.
    """
    client = get_redis_client()
    if client is None:
        return None  # Graceful fallback: Redis is down, we must hit Postgres/SQLite
    
    try:
        cached_data = client.get(f"idempotency:{idempotency_key}")
        if cached_data:
            return json.loads(cached_data)
    except Exception as e:
        logger.error(f"Redis READ error: {e}")
        
    return None


def set_idempotent_transaction(idempotency_key: str, transaction_dict: dict) -> None:
    """
    Store the complete transaction response dict in Redis, tied
    to the requested idempotency_key.
    
    This acts as a high-speed circuit-breaker for retries.
    """
    client = get_redis_client()
    if client is None or not idempotency_key:
        return
        
    try:
        # We ensure json serialization can happen
        payload = json.dumps(transaction_dict)
        client.setex(
            name=f"idempotency:{idempotency_key}",
            time=IDEMPOTENCY_TTL,
            value=payload
        )
    except Exception as e:
        logger.error(f"Redis WRITE error: {e}")
