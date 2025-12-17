"""
Company initialization controller.

Handles fetching data from ERP bootstrap API and storing in MongoDB.
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import HTTPException
from models.company import (
    Company, Project, Supplier, Module, CompanyInfo,
    InitRequest, InitResponse, ProjectStatus, SupplierType
)
from services.database import db_service
from services.erp_service import ERPService
import logging

logger = logging.getLogger(__name__)


class InitController:
    """Controller for company initialization"""

    def __init__(self):
        self.erp_service = ERPService()

    async def init_company(self, request: InitRequest) -> InitResponse:
        """
        Initialize a company by fetching data from ERP and storing in MongoDB.
        
        Args:
            request: InitRequest with company_id and force_refresh flag
            
        Returns:
            InitResponse with synchronized data
        """
        try:
            # Check if company already exists and refresh is not forced
            if not request.force_refresh:
                existing_company = await db_service.get_company(request.company_id)
                if existing_company:
                    return InitResponse(
                        success=True,
                        message="Company already initialized",
                        company_id=existing_company.company_id,
                        company_name=existing_company.name,
                        project_count=len(existing_company.projects),
                        supplier_count=len(existing_company.suppliers),
                        module_count=len(existing_company.modules),
                        projects=[
                            {
                                "project_id": p.project_id,
                                "name": p.name,
                                "status": p.status.value,
                            }
                            for p in existing_company.projects
                        ],
                    )

            # Fetch data from ERP bootstrap API
            logger.info(f"Fetching bootstrap data for company {request.company_id}")
            bootstrap_data = await self.erp_service.fetch_bootstrap(request.company_id)

            if not bootstrap_data.get("success"):
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to fetch data from ERP: {bootstrap_data.get('error', 'Unknown error')}"
                )

            data = bootstrap_data.get("data", {})

            # Parse company info
            company_info_data = data.get("company", {})
            company_info = CompanyInfo(
                name=company_info_data.get("name", f"Company {request.company_id}"),
                email=company_info_data.get("email"),
                phone=company_info_data.get("phone"),
                address=company_info_data.get("address"),
                city=company_info_data.get("city"),
                state=company_info_data.get("state"),
                country=company_info_data.get("country"),
                logo=company_info_data.get("logo"),
            )

            # Parse projects
            projects = []
            for proj in data.get("projects", []):
                # Determine status
                status = ProjectStatus.ACTIVE if proj.get("status") == 1 else ProjectStatus.INACTIVE
                
                # Generate keywords from project name
                name = proj.get("name", "")
                keywords = self._generate_keywords(name)
                
                projects.append(Project(
                    project_id=str(proj.get("id")),
                    name=name,
                    status=status,
                    keywords=keywords,
                    aliases=[],  # Can be populated later
                    metadata={"erp_status": proj.get("status")},
                ))

            # Parse suppliers
            suppliers = []
            for sup in data.get("suppliers", []):
                # Map supplier type
                sup_type = None
                type_str = sup.get("type")
                if type_str:
                    type_mapping = {
                        "material": SupplierType.MATERIAL,
                        "contract": SupplierType.CONTRACT,
                        "client": SupplierType.CLIENT,
                    }
                    sup_type = type_mapping.get(type_str.lower(), SupplierType.OTHER)

                suppliers.append(Supplier(
                    supplier_id=str(sup.get("id")),
                    name=sup.get("name", ""),
                    type=sup_type,
                    metadata={"erp_type": type_str},
                ))

            # Parse modules
            modules = []
            for mod in data.get("modules", []):
                modules.append(Module(
                    module_id=str(mod.get("id")),
                    name=mod.get("name", ""),
                    enabled=True,
                ))

            # Create company object
            company = Company(
                company_id=request.company_id,
                name=company_info.name,
                info=company_info,
                projects=projects,
                suppliers=suppliers,
                modules=modules,
                default_project_id=projects[0].project_id if projects else None,
                last_synced_at=datetime.utcnow(),
                metadata={
                    "user_id": data.get("user_id"),
                    "api_version": data.get("meta", {}).get("version"),
                },
            )

            # Upsert to database
            await db_service.upsert_company(company)

            logger.info(
                f"Initialized company {request.company_id}: "
                f"{len(projects)} projects, {len(suppliers)} suppliers, {len(modules)} modules"
            )

            return InitResponse(
                success=True,
                message=f"Company initialized successfully with {len(projects)} projects",
                company_id=company.company_id,
                company_name=company.name,
                project_count=len(projects),
                supplier_count=len(suppliers),
                module_count=len(modules),
                projects=[
                    {
                        "project_id": p.project_id,
                        "name": p.name,
                        "status": p.status.value,
                    }
                    for p in projects
                ],
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error initializing company: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error initializing company: {str(e)}"
            )

    def _generate_keywords(self, name: str) -> list:
        """Generate keywords from project name for better matching"""
        if not name:
            return []
        
        # Split name into words and filter short words
        words = name.lower().split()
        keywords = [w for w in words if len(w) > 2]
        
        # Add the full name as a keyword
        keywords.append(name.lower())
        
        return list(set(keywords))

