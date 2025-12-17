"""
Health check controller.
"""

from datetime import datetime
from typing import Dict, Any
from config import settings
from services.database import db_service
import logging

logger = logging.getLogger(__name__)


class HealthController:
    """Controller for health check endpoints"""

    async def get_root(self) -> Dict[str, Any]:
        """Get root endpoint information"""
        return {
            "message": settings.app_name,
            "version": settings.app_version,
            "documentation": "/docs",
            "health": "/health",
        }

    async def get_health(self) -> Dict[str, Any]:
        """Get health status of the application"""
        from services.agent_service import AgentService
        
        agent_service = AgentService()
        db_health = await db_service.health_check()

        return {
            "status": "healthy" if db_health["status"] == "healthy" else "degraded",
            "version": settings.app_version,
            "timestamp": datetime.utcnow().isoformat(),
            "apis_loaded": len(agent_service.get_all_apis()),
            "database": db_health,
        }

