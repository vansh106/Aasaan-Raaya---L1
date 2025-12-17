"""
Company management controller.
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException
from services.database import db_service
import logging

logger = logging.getLogger(__name__)


class CompanyController:
    """Controller for company management"""

    async def get_company(self, company_id: str) -> Dict[str, Any]:
        """Get company details including all projects"""
        company = await db_service.get_company(company_id)

        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company {company_id} not found. Please call /api/init first."
            )

        return {
            "company_id": company.company_id,
            "name": company.name,
            "project_count": len(company.projects),
            "supplier_count": len(company.suppliers),
            "module_count": len(company.modules),
            "projects": [
                {
                    "project_id": p.project_id,
                    "name": p.name,
                    "status": p.status.value,
                    "description": p.description,
                    "location": p.location,
                }
                for p in company.projects
            ],
        }

    async def list_projects(
        self,
        company_id: str,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all projects for a company"""
        company = await db_service.get_company(company_id)

        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company {company_id} not found"
            )

        projects = company.projects

        if status:
            projects = [p for p in projects if p.status.value == status]

        return {
            "company_id": company_id,
            "projects": [
                {
                    "project_id": p.project_id,
                    "name": p.name,
                    "status": p.status.value,
                    "description": p.description,
                    "keywords": p.keywords,
                }
                for p in projects
            ],
            "count": len(projects),
        }

    async def list_suppliers(
        self,
        company_id: str,
        type_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all suppliers for a company"""
        company = await db_service.get_company(company_id)

        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company {company_id} not found"
            )

        suppliers = company.suppliers

        if type_filter:
            suppliers = [s for s in suppliers if s.type and s.type.value == type_filter]

        return {
            "company_id": company_id,
            "suppliers": [
                {
                    "supplier_id": s.supplier_id,
                    "name": s.name,
                    "type": s.type.value if s.type else None,
                }
                for s in suppliers
            ],
            "count": len(suppliers),
        }

    async def list_modules(self, company_id: str) -> Dict[str, Any]:
        """List all ERP modules for a company"""
        company = await db_service.get_company(company_id)

        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company {company_id} not found"
            )

        return {
            "company_id": company_id,
            "modules": [
                {
                    "module_id": m.module_id,
                    "name": m.name,
                    "enabled": m.enabled,
                }
                for m in company.modules
            ],
            "count": len(company.modules),
        }

    async def set_default_project(
        self,
        company_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """Set the default project for a company"""
        # Verify company exists
        company = await db_service.get_company(company_id)
        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company {company_id} not found"
            )

        # Verify project exists in company
        project = company.get_project_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found in company {company_id}",
            )

        # Set default
        await db_service.set_default_project(company_id, project_id)

        return {
            "success": True,
            "message": f"Default project set to {project.name}",
            "company_id": company_id,
            "default_project_id": project_id,
            "default_project_name": project.name,
        }

