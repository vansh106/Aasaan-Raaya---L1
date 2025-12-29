"""
API catalog management routes.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from models.api_catalog import APIDefinition
from controllers.api_controller import APIController
from middleware.auth import get_api_key

router = APIRouter()
controller = APIController()


class APIListResponse(BaseModel):
    """API catalog list response model"""
    apis: List[Dict[str, Any]] = Field(..., description="List of all available ERP APIs")
    count: int = Field(..., description="Total number of APIs in the catalog")

    class Config:
        json_schema_extra = {
            "example": {
                "apis": [
                    {
                        "id": "get_supplier_payments",
                        "name": "Get Supplier Payment Details",
                        "description": "Retrieve all payment transactions for suppliers",
                        "endpoint": "/api/v1/suppliers/payments",
                        "method": "GET",
                        "tags": ["suppliers", "payments", "financial"]
                    },
                    {
                        "id": "get_project_materials",
                        "name": "Get Project Materials",
                        "description": "Fetch material inventory for a project",
                        "endpoint": "/api/v1/projects/{project_id}/materials",
                        "method": "GET",
                        "tags": ["materials", "inventory", "project"]
                    }
                ],
                "count": 15
            }
        }


@router.get(
    "/apis",
    response_model=APIListResponse,
    summary="List all available APIs",
    tags=["apis"],
    responses={
        200: {
            "description": "List of all APIs in the catalog",
            "content": {
                "application/json": {
                    "example": {
                        "apis": [
                            {
                                "id": "get_supplier_payments",
                                "name": "Get Supplier Payment Details",
                                "description": "Retrieve all payment transactions for suppliers",
                                "endpoint": "/api/v1/suppliers/payments",
                                "method": "GET",
                                "tags": ["suppliers", "payments", "financial"]
                            }
                        ],
                        "count": 15
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - invalid API key"
        }
    }
)
async def get_apis(api_key: str = Depends(get_api_key)):
    """
    Get all available APIs from the catalog.
    
    Returns a comprehensive list of all ERP APIs that the chatbot can query.
    Each API definition includes:
    - Unique identifier
    - Name and description
    - Endpoint URL and HTTP method
    - Required parameters
    - Tags for categorization
    - Example use cases
    
    ## Authentication:
    Requires valid API key in the `X-API-Key` header.
    """
    return await controller.list_apis()


@router.post(
    "/apis",
    summary="Add new API to catalog",
    tags=["apis"],
    responses={
        200: {
            "description": "API added successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "API added to catalog",
                        "api_id": "new_api_id"
                    }
                }
            }
        },
        400: {
            "description": "Bad request - invalid API definition"
        },
        401: {
            "description": "Unauthorized - invalid API key"
        }
    }
)
async def add_api(
    api_definition: APIDefinition,
    api_key: str = Depends(get_api_key)
):
    """
    Add a new API to the catalog.
    
    This allows dynamic registration of new ERP endpoints that the chatbot can use.
    
    ## Required Fields:
    - **id**: Unique identifier for the API
    - **name**: Human-readable name
    - **description**: Detailed description of what the API does
    - **endpoint**: API endpoint path
    - **method**: HTTP method (GET, POST, PUT, DELETE, PATCH)
    - **parameters**: List of parameters the API accepts
    - **tags**: Tags for categorization
    - **response_description**: Description of the response structure
    
    ## Authentication:
    Requires valid API key in the `X-API-Key` header.
    """
    return await controller.add_api(api_definition)


@router.post(
    "/apis/reload",
    summary="Reload API catalog from disk",
    tags=["apis"],
    responses={
        200: {
            "description": "Catalog reloaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "API catalog reloaded",
                        "count": 15
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - invalid API key"
        },
        500: {
            "description": "Server error - failed to reload catalog"
        }
    }
)
async def reload_apis(api_key: str = Depends(get_api_key)):
    """
    Reload the API catalog from the JSON file.
    
    Useful after manually editing the `api_catalog.json` file to add or modify API definitions.
    This endpoint reloads the entire catalog from disk without restarting the server.
    
    ## Authentication:
    Requires valid API key in the `X-API-Key` header.
    """
    return await controller.reload_catalog()

