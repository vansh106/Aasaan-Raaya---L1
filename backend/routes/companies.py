"""
Company management routes.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from controllers.company_controller import CompanyController
from middleware.auth import get_api_key

router = APIRouter()
controller = CompanyController()


class ProjectResponse(BaseModel):
    """Project response model"""
    project_id: str
    name: str
    status: str
    description: Optional[str] = None
    location: Optional[str] = None


class SupplierResponse(BaseModel):
    """Supplier response model"""
    supplier_id: str
    name: str
    type: Optional[str] = None


class ModuleResponse(BaseModel):
    """Module response model"""
    module_id: str
    name: str
    enabled: bool = True


class CompanyResponse(BaseModel):
    """Company response model"""
    company_id: str
    name: str
    project_count: int
    supplier_count: int
    module_count: int
    projects: List[ProjectResponse]


@router.get(
    "/companies/{company_id}",
    response_model=CompanyResponse,
    summary="Get company details"
)
async def get_company(
    company_id: str,
    api_key: str = Depends(get_api_key)
):
    """Get company details including all projects."""
    return await controller.get_company(company_id)


@router.get(
    "/companies/{company_id}/projects",
    summary="List company projects"
)
async def list_projects(
    company_id: str,
    status: Optional[str] = Query(
        None, description="Filter by status (active, inactive, completed)"
    ),
    api_key: str = Depends(get_api_key),
):
    """
    List all projects for a company.
    
    Optionally filter by project status.
    """
    return await controller.list_projects(company_id, status)


@router.get(
    "/companies/{company_id}/suppliers",
    summary="List company suppliers"
)
async def list_suppliers(
    company_id: str,
    type: Optional[str] = Query(
        None, description="Filter by type (material, contract, client)"
    ),
    api_key: str = Depends(get_api_key),
):
    """
    List all suppliers for a company.
    
    Optionally filter by supplier type.
    """
    return await controller.list_suppliers(company_id, type)


@router.get(
    "/companies/{company_id}/modules",
    summary="List company modules"
)
async def list_modules(
    company_id: str,
    api_key: str = Depends(get_api_key),
):
    """List all ERP modules enabled for a company."""
    return await controller.list_modules(company_id)


@router.put(
    "/companies/{company_id}/default-project",
    summary="Set default project"
)
async def set_default_project(
    company_id: str,
    project_id: str = Query(..., description="Project ID to set as default"),
    api_key: str = Depends(get_api_key),
):
    """
    Set the default project for a company.
    
    The default project is used when queries don't specify a project.
    """
    return await controller.set_default_project(company_id, project_id)

