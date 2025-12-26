"""
Chat history service

Responsibilities:
- Manage chat sessions across MongoDB and Redis
- Keep recent exchanges in Redis for low latency
- Flush buffered exchanges to MongoDB with a write-behind strategy
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional

from config import settings
from services.database import db_service
from services.redis_service import redis_service
import logging

logger = logging.getLogger(__name__)


class ChatHistoryService:
    """Persist and retrieve chat history with Redis write-behind buffering."""

    def __init__(self):
        self._flush_tasks: Dict[str, asyncio.Task] = {}

    # -------------------- Key helpers -------------------- #
    def _buffer_key(self, session_id: str) -> str:
        return f"chat:session:{session_id}:buffer"

    # -------------------- Public API -------------------- #
    async def get_or_create_session(
        self, session_id: str, company_id: Optional[str]
    ) -> Dict:
        """
        Fetch chat session from MongoDB; create if missing.
        Does not write chat messages here (write-behind handles that).
        """
        session = await db_service.db.chat_sessions.find_one({"session_id": session_id})
        if session:
            session.pop("_id", None)
            return session

        doc = {
            "session_id": session_id,
            "company_id": company_id,
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
        }
        await db_service.db.chat_sessions.insert_one(doc)
        logger.info(f"Created new chat session: {session_id}")
        return doc

    async def load_history(
        self, session_id: str, company_id: Optional[str]
    ) -> List[Dict[str, str]]:
        """
        Get combined chat history: persisted Mongo + buffered Redis entries.
        """
        session = await self.get_or_create_session(session_id, company_id)
        persisted = session.get("messages", [])

        # Load buffered exchanges from Redis
        buffered_raw = await redis_service.list_get_all(self._buffer_key(session_id))
        buffered: List[Dict[str, str]] = []
        for item in buffered_raw:
            try:
                buffered.append(json.loads(item))
            except Exception:
                logger.warning("Failed to parse buffered chat entry", exc_info=True)

        return persisted + buffered

    async def append_exchange(
        self, session_id: str, company_id: Optional[str], user_query: str, llm_response: str
    ):
        """
        Append user + assistant messages to Redis buffer and schedule write-behind flush.
        """
        messages = [
            {"role": "user", "content": user_query, "timestamp": datetime.utcnow().isoformat()},
            {"role": "assistant", "content": llm_response, "timestamp": datetime.utcnow().isoformat()},
        ]

        # Serialize for Redis list
        serialized = [json.dumps(m) for m in messages]
        ttl = settings.chat_history_ttl_seconds
        await redis_service.list_append(self._buffer_key(session_id), serialized, ttl=ttl)

        # Touch session last_activity in Mongo for TTL housekeeping
        await db_service.db.chat_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"last_activity": datetime.utcnow(), "company_id": company_id}},
        )

        # Schedule background flush to Mongo
        await self._schedule_flush(session_id)

    # -------------------- Write-behind flushing -------------------- #
    async def _schedule_flush(self, session_id: str):
        """Debounce flush tasks per session."""
        if session_id in self._flush_tasks:
            return

        delay = max(1, settings.chat_write_behind_delay_seconds)

        async def _delayed():
            try:
                await asyncio.sleep(delay)
                await self.flush_buffer_to_mongo(session_id)
            finally:
                self._flush_tasks.pop(session_id, None)

        task = asyncio.create_task(_delayed())
        self._flush_tasks[session_id] = task

    async def flush_buffer_to_mongo(self, session_id: str):
        """Move buffered exchanges from Redis into MongoDB."""
        buffered_raw = await redis_service.list_pop_all(self._buffer_key(session_id))
        if not buffered_raw:
            return

        messages = []
        for item in buffered_raw:
            try:
                messages.append(json.loads(item))
            except Exception:
                logger.warning("Failed to parse buffered chat entry during flush", exc_info=True)

        if not messages:
            return

        now = datetime.utcnow()
        await db_service.db.chat_sessions.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": {"$each": messages}},
                "$set": {"updated_at": now, "last_activity": now},
            },
            upsert=True,
        )
        logger.info(f"Flushed {len(messages)} chat messages to Mongo for session {session_id}")


# Global instance
chat_history_service = ChatHistoryService()

