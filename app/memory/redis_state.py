"""
redis_state.py
==============
LAYER: Memory — Redis State Persistence

Persists agent sessions and intermediate state to Redis.
Agents can resume mid-workflow after failures.
Session TTL: 1 hour (configurable).
"""

import json
import logging
from typing import Optional, Any
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)


class RedisStateManager:
    """
    Async Redis state manager for agent sessions.

    Key schema:
      session:{session_id}:state   → full AgentState snapshot
      session:{session_id}:meta    → session metadata (created_at, tx_id)
    """

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    async def get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._client

    async def save_state(self, session_id: str, state: dict) -> None:
        """Save agent state snapshot to Redis with TTL."""
        client = await self.get_client()
        key = f"session:{session_id}:state"
        try:
            serialised = json.dumps(state, default=str)
            await client.setex(key, settings.redis_ttl_seconds, serialised)
            logger.debug(f"[REDIS] Saved state for session {session_id}")
        except Exception as e:
            logger.error(f"[REDIS] Failed to save state: {e}")

    async def load_state(self, session_id: str) -> Optional[dict]:
        """Load agent state from Redis."""
        client = await self.get_client()
        key = f"session:{session_id}:state"
        try:
            data = await client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"[REDIS] Failed to load state: {e}")
            return None

    async def delete_state(self, session_id: str) -> None:
        """Delete session state (cleanup after completion)."""
        client = await self.get_client()
        await client.delete(f"session:{session_id}:state", f"session:{session_id}:meta")

    async def session_exists(self, session_id: str) -> bool:
        """Check if a session is still active in Redis."""
        client = await self.get_client()
        return bool(await client.exists(f"session:{session_id}:state"))

    async def health_check(self) -> bool:
        """Ping Redis to verify connectivity."""
        try:
            client = await self.get_client()
            return await client.ping()
        except Exception:
            return False


state_manager = RedisStateManager()
