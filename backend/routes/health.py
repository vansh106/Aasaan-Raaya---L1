"""
Health check routes.
"""

from fastapi import APIRouter
from controllers.health_controller import HealthController

router = APIRouter()
controller = HealthController()


@router.get(
    "/",
    summary="Root endpoint",
    tags=["health"],
    responses={
        200: {
            "description": "API information and welcome message",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Welcome to ERP Agentic Chatbot API",
                        "version": "1.0.0",
                        "docs": "/docs",
                        "health": "/health"
                    }
                }
            }
        }
    }
)
async def root():
    """
    Root endpoint with API information.
    
    Returns basic information about the API including:
    - API name and version
    - Links to documentation
    - Health check endpoint
    
    This endpoint does not require authentication.
    """
    return await controller.get_root()


@router.get(
    "/health",
    summary="Health check",
    tags=["health"],
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "services": {
                            "database": "connected",
                            "redis": "connected",
                            "llm": "operational"
                        },
                        "version": "1.0.0"
                    }
                }
            }
        },
        503: {
            "description": "Service is unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "services": {
                            "database": "disconnected",
                            "redis": "disconnected",
                            "llm": "error"
                        }
                    }
                }
            }
        }
    }
)
async def health_check():
    """
    Health check endpoint.
    
    Returns the current health status of the API and its dependencies including:
    - Overall service status
    - Database connection status
    - Redis connection status
    - LLM service status
    - API version
    - Timestamp
    
    This endpoint does not require authentication and can be used for:
    - Load balancer health checks
    - Monitoring and alerting
    - Service discovery
    - Debugging connection issues
    """
    return await controller.get_health()

