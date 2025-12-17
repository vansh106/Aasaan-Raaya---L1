"""
API catalog controller.
"""

from typing import Dict, Any
from fastapi import HTTPException
from models.api_catalog import APIDefinition
from services.agent_service import AgentService
import logging

logger = logging.getLogger(__name__)

# Singleton agent service
_agent_service = None


def get_agent_service() -> AgentService:
    """Get or create agent service instance"""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service


class APIController:
    """Controller for API catalog management"""

    async def list_apis(self) -> Dict[str, Any]:
        """List all available APIs"""
        try:
            agent_service = get_agent_service()
            apis = agent_service.get_all_apis()
            return {
                "apis": [api.model_dump() for api in apis],
                "count": len(apis)
            }
        except Exception as e:
            logger.error(f"Error fetching APIs: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching APIs: {str(e)}"
            )

    async def add_api(self, api_definition: APIDefinition) -> Dict[str, Any]:
        """Add a new API to the catalog"""
        try:
            agent_service = get_agent_service()
            success = agent_service.add_api_to_catalog(api_definition)

            if success:
                return {
                    "success": True,
                    "message": "API added successfully",
                    "api_id": api_definition.id,
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to add API to catalog"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding API: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error adding API: {str(e)}"
            )

    async def reload_catalog(self) -> Dict[str, Any]:
        """Reload API catalog from disk"""
        try:
            agent_service = get_agent_service()
            agent_service.reload_catalog()
            apis = agent_service.get_all_apis()
            return {
                "success": True,
                "message": "API catalog reloaded",
                "apis_loaded": len(apis),
            }
        except Exception as e:
            logger.error(f"Error reloading APIs: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error reloading APIs: {str(e)}"
            )

