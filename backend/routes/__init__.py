"""
Routes package - API endpoint definitions.
"""

from fastapi import APIRouter
from routes.health import router as health_router
from routes.init import router as init_router
from routes.chat import router as chat_router
from routes.apis import router as apis_router
from routes.companies import router as companies_router

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(health_router, tags=["health"])
api_router.include_router(init_router, prefix="/api", tags=["init"])
api_router.include_router(chat_router, prefix="/api", tags=["chat"])
api_router.include_router(apis_router, prefix="/api", tags=["apis"])
api_router.include_router(companies_router, prefix="/api", tags=["companies"])

__all__ = ["api_router"]

