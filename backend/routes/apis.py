"""
API catalog management routes.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from models.api_catalog import APIDefinition
from controllers.api_controller import APIController
from middleware.auth import get_api_key

router = APIRouter()
controller = APIController()


class APIListResponse(BaseModel):
    """API list response model"""
    apis: List[Dict[str, Any]]
    count: int


@router.get(
    "/apis",
    response_model=APIListResponse,
    summary="List all available APIs"
)
async def get_apis(api_key: str = Depends(get_api_key)):
    """
    Get all available APIs from the catalog.
    
    Returns a list of all ERP APIs that the chatbot can query.
    """
    return await controller.list_apis()


@router.post("/apis", summary="Add new API to catalog")
async def add_api(
    api_definition: APIDefinition,
    api_key: str = Depends(get_api_key)
):
    """
    Add a new API to the catalog.
    
    This allows dynamic registration of new ERP endpoints.
    """
    return await controller.add_api(api_definition)


@router.post("/apis/reload", summary="Reload API catalog from disk")
async def reload_apis(api_key: str = Depends(get_api_key)):
    """
    Reload the API catalog from the JSON file.
    
    Useful after manually editing the api_catalog.json file.
    """
    return await controller.reload_catalog()

