"""
Health check routes.
"""

from fastapi import APIRouter
from controllers.health_controller import HealthController

router = APIRouter()
controller = HealthController()


@router.get("/", summary="Root endpoint")
async def root():
    """Root endpoint with API information"""
    return await controller.get_root()


@router.get("/health", summary="Health check")
async def health_check():
    """
    Health check endpoint.
    
    Returns the current health status of the API and its dependencies.
    """
    return await controller.get_health()

