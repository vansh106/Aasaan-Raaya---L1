"""
Company initialization routes.
"""

from fastapi import APIRouter, Depends
from models.company import InitRequest, InitResponse
from controllers.init_controller import InitController
from middleware.auth import get_api_key

router = APIRouter()
controller = InitController()


@router.post(
    "/init",
    response_model=InitResponse,
    summary="Initialize company and sync projects",
    tags=["init"],
    responses={
        200: {
            "description": "Company initialized successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Company initialized successfully",
                        "company_id": "88",
                        "company_name": "Parekh Construction",
                        "project_count": 11,
                        "supplier_count": 85,
                        "module_count": 8,
                        "projects": [
                            {
                                "project_id": "165",
                                "name": "Paradise apartments",
                                "status": "active"
                            },
                            {
                                "project_id": "178",
                                "name": "Elanza Heights",
                                "status": "active"
                            }
                        ]
                    }
                }
            }
        },
        400: {
            "description": "Bad request - invalid company_id",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "Invalid company_id"
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - invalid API key",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {"message": "Invalid API key"}
                    }
                }
            }
        },
        500: {
            "description": "Server error - failed to sync with ERP",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {"message": "Failed to fetch data from ERP"}
                    }
                }
            }
        }
    }
)
async def init_company(
    request: InitRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Initialize a company and sync its data from ERP.
    
    This endpoint should be called when a user logs into the ERP system.
    It will:
    1. Call the ERP bootstrap API to fetch company data
    2. Store projects, suppliers, and modules in MongoDB
    3. Return the synchronized data
    
    **Usage**: Call this on every user login to ensure data is up-to-date.
    
    ## Parameters:
    - **company_id**: The unique identifier of the company in your ERP system
    - **force_refresh**: Set to `true` to force refresh even if data was recently synced
    
    ## Response:
    Returns comprehensive company information including:
    - All projects associated with the company
    - All suppliers/vendors
    - Enabled ERP modules
    - Project counts and metadata
    
    ## Authentication:
    Requires valid API key in the `X-API-Key` header.
    """
    return await controller.init_company(request)

