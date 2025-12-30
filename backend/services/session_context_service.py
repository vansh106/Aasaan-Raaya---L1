"""
Session Context Service

Manages session-level context like selected project, user preferences, etc.
Stores in Redis for fast access across requests.
"""

import json
from typing import Dict, Any, Optional
from services.redis_service import redis_service
from config import settings
import logging

logger = logging.getLogger(__name__)


class SessionContextService:
    """Manages session context storage in Redis"""

    def _context_key(self, session_id: str) -> str:
        """Generate Redis key for session context"""
        return f"chat:session:{session_id}:context"

    async def get_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get session context from Redis.
        
        Returns:
            Dictionary with context data (e.g., project_id, project_name)
        """
        try:
            context_json = await redis_service.get(self._context_key(session_id))
            if context_json:
                return json.loads(context_json)
            return {}
        except Exception as e:
            logger.warning(f"Failed to load session context: {e}")
            return {}

    async def update_context(
        self, session_id: str, updates: Dict[str, Any]
    ) -> None:
        """
        Update session context with new data.
        
        Args:
            session_id: Session ID
            updates: Dictionary of fields to update
        """
        try:
            # Get existing context
            context = await self.get_context(session_id)
            
            # Merge updates
            context.update(updates)
            
            # Save back to Redis with TTL
            ttl = settings.chat_history_ttl_seconds
            await redis_service.set(
                self._context_key(session_id),
                json.dumps(context),
                ttl=ttl
            )
            
            logger.info(f"Updated session context for {session_id}: {updates}")
        except Exception as e:
            logger.error(f"Failed to update session context: {e}")

    async def set_project(
        self, session_id: str, project_id: str, project_name: str
    ) -> None:
        """
        Store selected project in session context.
        
        Args:
            session_id: Session ID
            project_id: Project ID
            project_name: Project name
        """
        await self.update_context(
            session_id,
            {
                "project_id": project_id,
                "project_name": project_name,
            }
        )

    async def get_project(self, session_id: str) -> Optional[Dict[str, str]]:
        """
        Get stored project from session context.
        
        Returns:
            Dictionary with project_id and project_name, or None
        """
        context = await self.get_context(session_id)
        if "project_id" in context and "project_name" in context:
            return {
                "project_id": context["project_id"],
                "project_name": context["project_name"],
            }
        return None

    async def clear_context(self, session_id: str) -> None:
        """Clear session context"""
        try:
            await redis_service.delete(self._context_key(session_id))
            logger.info(f"Cleared session context for {session_id}")
        except Exception as e:
            logger.error(f"Failed to clear session context: {e}")


# Global instance
session_context_service = SessionContextService()

