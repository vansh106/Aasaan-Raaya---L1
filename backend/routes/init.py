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
    summary="Initialize company and sync projects"
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
    """
    return await controller.init_company(request)

