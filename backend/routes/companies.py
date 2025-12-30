"""
Company management routes.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from controllers.company_controller import CompanyController
from middleware.auth import get_api_key

router = APIRouter()
controller = CompanyController()


class ProjectResponse(BaseModel):
    """Project response model"""
    project_id: str = Field(..., description="Unique project identifier from ERP")
    name: str = Field(..., description="Project name")
    status: str = Field(..., description="Project status (active, inactive, completed, on_hold)")
    description: Optional[str] = Field(None, description="Project description")
    location: Optional[str] = Field(None, description="Project location or address")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "165",
                "name": "Paradise apartments",
                "status": "active",
                "description": "Luxury residential project",
                "location": "Mumbai"
            }
        }


class SupplierResponse(BaseModel):
    """Supplier response model"""
    supplier_id: str = Field(..., description="Unique supplier identifier from ERP")
    name: str = Field(..., description="Supplier/vendor name")
    type: Optional[str] = Field(None, description="Supplier type (material, contract, client, other)")

    class Config:
        json_schema_extra = {
            "example": {
                "supplier_id": "1790",
                "name": "Alpha Structures",
                "type": "contract"
            }
        }


class ModuleResponse(BaseModel):
    """Module response model"""
    module_id: str = Field(..., description="Unique module identifier from ERP")
    name: str = Field(..., description="Module name (e.g., Attendance & Payroll)")
    enabled: bool = Field(True, description="Whether the module is enabled for this company")

    class Config:
        json_schema_extra = {
            "example": {
                "module_id": "1",
                "name": "Attendance & Payroll",
                "enabled": True
            }
        }


class CompanyResponse(BaseModel):
    """Company response model with all related data"""
    company_id: str = Field(..., description="Unique company identifier from ERP")
    name: str = Field(..., description="Company name")
    project_count: int = Field(..., description="Total number of projects")
    supplier_count: int = Field(..., description="Total number of suppliers/vendors")
    module_count: int = Field(..., description="Total number of enabled ERP modules")
    projects: List[ProjectResponse] = Field(..., description="List of all company projects")

    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "88",
                "name": "Parekh Construction",
                "project_count": 11,
                "supplier_count": 85,
                "module_count": 8,
                "projects": [
                    {
                        "project_id": "165",
                        "name": "Paradise apartments",
                        "status": "active",
                        "location": "Mumbai"
                    }
                ]
            }
        }


@router.get(
    "/companies/{company_id}",
    response_model=CompanyResponse,
    summary="Get company details",
    tags=["companies"],
    responses={
        200: {
            "description": "Company details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "company_id": "88",
                        "name": "Parekh Construction",
                        "project_count": 11,
                        "supplier_count": 85,
                        "module_count": 8,
                        "projects": [
                            {
                                "project_id": "165",
                                "name": "Paradise apartments",
                                "status": "active",
                                "location": "Mumbai"
                            }
                        ]
                    }
                }
            }
        },
        404: {
            "description": "Company not found"
        },
        401: {
            "description": "Unauthorized - invalid API key"
        }
    }
)
async def get_company(
    company_id: str,
    api_key: str = Depends(get_api_key)
):
    """
    Get comprehensive company details including all projects.
    
    Returns complete information about a company including:
    - Company metadata (name, contact info, etc.)
    - Count of projects, suppliers, and modules
    - List of all projects with their details
    
    ## Authentication:
    Requires valid API key in the `X-API-Key` header.
    """
    return await controller.get_company(company_id)


@router.get(
    "/companies/{company_id}/projects",
    summary="List company projects",
    tags=["companies"],
    responses={
        200: {
            "description": "List of projects",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "projects": [
                            {
                                "project_id": "165",
                                "name": "Paradise apartments",
                                "status": "active",
                                "description": "Luxury residential project",
                                "location": "Mumbai"
                            }
                        ],
                        "count": 11
                    }
                }
            }
        },
        404: {
            "description": "Company not found"
        },
        401: {
            "description": "Unauthorized - invalid API key"
        }
    }
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
    
    Returns all projects associated with the specified company.
    Optionally filter results by project status.
    
    ## Query Parameters:
    - **status**: Filter projects by status
      - `active` - Currently active projects
      - `inactive` - Temporarily inactive projects
      - `completed` - Completed projects
      - `on_hold` - Projects on hold
    
    ## Authentication:
    Requires valid API key in the `X-API-Key` header.
    """
    return await controller.list_projects(company_id, status)


@router.get(
    "/companies/{company_id}/suppliers",
    summary="List company suppliers",
    tags=["companies"],
    responses={
        200: {
            "description": "List of suppliers",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "suppliers": [
                            {
                                "supplier_id": "1790",
                                "name": "Alpha Structures",
                                "type": "contract",
                                "contact": "+91-9876543210"
                            }
                        ],
                        "count": 85
                    }
                }
            }
        },
        404: {
            "description": "Company not found"
        },
        401: {
            "description": "Unauthorized - invalid API key"
        }
    }
)
async def list_suppliers(
    company_id: str,
    type: Optional[str] = Query(
        None, description="Filter by type (material, contract, client)"
    ),
    api_key: str = Depends(get_api_key),
):
    """
    List all suppliers/vendors for a company.
    
    Returns all suppliers associated with the specified company.
    Optionally filter results by supplier type.
    
    ## Query Parameters:
    - **type**: Filter suppliers by type
      - `material` - Material suppliers
      - `contract` - Contractor suppliers
      - `client` - Client suppliers
      - `other` - Other types
    
    ## Authentication:
    Requires valid API key in the `X-API-Key` header.
    """
    return await controller.list_suppliers(company_id, type)


@router.get(
    "/companies/{company_id}/modules",
    summary="List company modules",
    tags=["companies"],
    responses={
        200: {
            "description": "List of ERP modules",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "modules": [
                            {
                                "module_id": "1",
                                "name": "Attendance & Payroll",
                                "enabled": True
                            },
                            {
                                "module_id": "2",
                                "name": "Inventory Management",
                                "enabled": True
                            }
                        ],
                        "count": 8
                    }
                }
            }
        },
        404: {
            "description": "Company not found"
        },
        401: {
            "description": "Unauthorized - invalid API key"
        }
    }
)
async def list_modules(
    company_id: str,
    api_key: str = Depends(get_api_key),
):
    """
    List all ERP modules enabled for a company.
    
    Returns all modules that are enabled and available for use with this company's ERP instance.
    
    ## Authentication:
    Requires valid API key in the `X-API-Key` header.
    """
    return await controller.list_modules(company_id)


@router.put(
    "/companies/{company_id}/default-project",
    summary="Set default project",
    tags=["companies"],
    responses={
        200: {
            "description": "Default project updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Default project updated",
                        "company_id": "88",
                        "default_project_id": "165"
                    }
                }
            }
        },
        404: {
            "description": "Company or project not found"
        },
        401: {
            "description": "Unauthorized - invalid API key"
        }
    }
)
async def set_default_project(
    company_id: str,
    project_id: str = Query(..., description="Project ID to set as default"),
    api_key: str = Depends(get_api_key),
):
    """
    Set the default project for a company.
    
    The default project is used when user queries don't explicitly specify a project.
    This is helpful for companies that primarily work on a single main project.
    
    ## Query Parameters:
    - **project_id**: The ID of the project to set as default
    
    ## Authentication:
    Requires valid API key in the `X-API-Key` header.
    """
    return await controller.set_default_project(company_id, project_id)

