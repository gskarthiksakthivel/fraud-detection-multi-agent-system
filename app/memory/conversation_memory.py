"""
conversation_memory.py
======================
LAYER: Memory — Conversation History

Manages multi-turn conversation context for the investigation agent.
Stores per-session message history in Redis with context window management.
Summarises older messages when context window approaches limit.
"""

import json
import logging
from typing import List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)

MAX_MESSAGES_BEFORE_SUMMARY = 20
SUMMARY_KEEP_RECENT = 5


class ConversationMemory:
    """
    Redis-backed conversation memory with automatic summarisation.

    When message count exceeds MAX_MESSAGES_BEFORE_SUMMARY:
    - Old messages are summarised via LLM
    - Summary is stored as a SystemMessage
    - Only SUMMARY_KEEP_RECENT recent messages are kept in full
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._client: Optional[redis.Redis] = None

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        return self._client

    def _key(self) -> str:
        return f"conversation:{self.session_id}:messages"

    async def add_message(self, message: BaseMessage) -> None:
        """Append a message to conversation history."""
        client = await self._get_client()
        msg_data = {"type": message.__class__.__name__, "content": message.content}
        await client.rpush(self._key(), json.dumps(msg_data))
        await client.expire(self._key(), settings.redis_ttl_seconds)

        count = await client.llen(self._key())
        if count > MAX_MESSAGES_BEFORE_SUMMARY:
            await self._summarise_old_messages()

    async def get_messages(self) -> List[BaseMessage]:
        """Retrieve full conversation history."""
        client = await self._get_client()
        raw = await client.lrange(self._key(), 0, -1)

        messages = []
        for item in raw:
            data = json.loads(item)
            msg_type = data.get("type", "HumanMessage")
            content = data.get("content", "")
            if msg_type == "HumanMessage":
                messages.append(HumanMessage(content=content))
            elif msg_type == "AIMessage":
                messages.append(AIMessage(content=content))
            elif msg_type == "SystemMessage":
                messages.append(SystemMessage(content=content))
        return messages

    async def _summarise_old_messages(self) -> None:
        """Summarise old messages and replace them with a summary SystemMessage."""
        messages = await self.get_messages()
        if len(messages) <= SUMMARY_KEEP_RECENT:
            return

        old_messages = messages[:-SUMMARY_KEEP_RECENT]
        recent_messages = messages[-SUMMARY_KEEP_RECENT:]

        llm = ChatOpenAI(model=settings.openai_model, temperature=0, api_key=settings.openai_api_key)
        summary_prompt = f"Summarise this fraud investigation conversation history concisely:\n" + \
                         "\n".join([f"{m.__class__.__name__}: {m.content}" for m in old_messages])

        summary_response = await llm.ainvoke([HumanMessage(content=summary_prompt)])
        summary_msg = SystemMessage(content=f"[CONVERSATION SUMMARY]: {summary_response.content}")

        client = await self._get_client()
        await client.delete(self._key())
        await client.rpush(self._key(), json.dumps({"type": "SystemMessage", "content": summary_msg.content}))
        for msg in recent_messages:
            await client.rpush(self._key(), json.dumps({"type": msg.__class__.__name__, "content": msg.content}))
        await client.expire(self._key(), settings.redis_ttl_seconds)
        logger.info(f"[MEMORY] Summarised {len(old_messages)} messages for session {self.session_id}")

    async def clear(self) -> None:
        client = await self._get_client()
        await client.delete(self._key())
