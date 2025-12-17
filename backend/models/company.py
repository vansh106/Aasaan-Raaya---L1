"""
Company, Project, Supplier, and Module models for MongoDB storage.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status enum"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class SupplierType(str, Enum):
    """Supplier type enum"""
    MATERIAL = "material"
    CONTRACT = "contract"
    CLIENT = "client"
    OTHER = "other"


class Project(BaseModel):
    """Project model representing a project within a company"""
    
    project_id: str = Field(..., description="Unique project identifier from ERP")
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE)
    location: Optional[str] = Field(None, description="Project location")
    start_date: Optional[datetime] = Field(None, description="Project start date")
    end_date: Optional[datetime] = Field(None, description="Project end date")
    
    # Keywords for LLM matching
    keywords: List[str] = Field(default_factory=list, description="Keywords for project matching")
    aliases: List[str] = Field(default_factory=list, description="Alternative names for the project")
    
    # Metadata from ERP
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional project metadata")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "165",
                "name": "Paradise apartments",
                "status": "active",
                "keywords": ["paradise", "apartments", "residential"]
            }
        }


class Supplier(BaseModel):
    """Supplier model representing a supplier/vendor"""
    
    supplier_id: str = Field(..., description="Unique supplier identifier from ERP")
    name: str = Field(..., description="Supplier name")
    type: Optional[SupplierType] = Field(None, description="Supplier type")
    
    # Additional info (can be extended)
    contact: Optional[str] = Field(None, description="Contact information")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    
    # Metadata from ERP
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "supplier_id": "1790",
                "name": "Alpha Structures",
                "type": "contract"
            }
        }


class Module(BaseModel):
    """ERP Module model"""
    
    module_id: str = Field(..., description="Unique module identifier from ERP")
    name: str = Field(..., description="Module name")
    description: Optional[str] = Field(None, description="Module description")
    enabled: bool = Field(default=True, description="Whether module is enabled")
    
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "module_id": "1",
                "name": "Attendance & Payroll",
                "enabled": True
            }
        }


class CompanyInfo(BaseModel):
    """Company information from ERP"""
    
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    logo: Optional[str] = None


class Company(BaseModel):
    """Company model containing projects, suppliers, and modules"""
    
    company_id: str = Field(..., description="Unique company identifier from ERP")
    name: str = Field(..., description="Company name")
    description: Optional[str] = Field(None, description="Company description")
    
    # Company info from ERP
    info: Optional[CompanyInfo] = Field(None, description="Detailed company info")
    
    # Projects belonging to this company
    projects: List[Project] = Field(default_factory=list, description="List of projects")
    
    # Suppliers associated with this company
    suppliers: List[Supplier] = Field(default_factory=list, description="List of suppliers")
    
    # ERP Modules enabled for this company
    modules: List[Module] = Field(default_factory=list, description="List of ERP modules")
    
    # Default project for queries without explicit project reference
    default_project_id: Optional[str] = Field(None, description="Default project ID")
    
    # API configuration specific to this company
    api_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_synced_at: Optional[datetime] = Field(None, description="Last sync from ERP")

    def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        for project in self.projects:
            if project.project_id == project_id:
                return project
        return None

    def get_project_by_name(self, name: str) -> Optional[Project]:
        """Get project by name (case-insensitive)"""
        name_lower = name.lower()
        for project in self.projects:
            if project.name.lower() == name_lower:
                return project
            if any(alias.lower() == name_lower for alias in project.aliases):
                return project
        return None

    def search_projects(self, query: str) -> List[Project]:
        """Search projects by name, keywords, or aliases"""
        query_lower = query.lower()
        results = []
        
        for project in self.projects:
            score = 0
            
            # Check name
            if query_lower in project.name.lower():
                score += 10
            
            # Check aliases
            for alias in project.aliases:
                if query_lower in alias.lower():
                    score += 8
            
            # Check keywords
            for keyword in project.keywords:
                if query_lower in keyword.lower():
                    score += 5
            
            # Check description
            if project.description and query_lower in project.description.lower():
                score += 3
            
            if score > 0:
                results.append((project, score))
        
        # Sort by score and return projects
        results.sort(key=lambda x: x[1], reverse=True)
        return [project for project, _ in results]

    def get_supplier_by_id(self, supplier_id: str) -> Optional[Supplier]:
        """Get supplier by ID"""
        for supplier in self.suppliers:
            if supplier.supplier_id == supplier_id:
                return supplier
        return None

    def get_suppliers_by_type(self, supplier_type: SupplierType) -> List[Supplier]:
        """Get suppliers by type"""
        return [s for s in self.suppliers if s.type == supplier_type]


# ==================== Request/Response Models ====================

class InitRequest(BaseModel):
    """Request model for company initialization"""
    company_id: str = Field(..., description="Company ID from ERP")
    force_refresh: bool = Field(False, description="Force refresh data from ERP")

    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "88",
                "force_refresh": False
            }
        }


class InitResponse(BaseModel):
    """Response model for company initialization"""
    success: bool
    message: str
    company_id: str
    company_name: str
    project_count: int
    supplier_count: int
    module_count: int
    projects: List[Dict[str, Any]]

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Company initialized successfully",
                "company_id": "88",
                "company_name": "Parekh Construction",
                "project_count": 11,
                "supplier_count": 85,
                "module_count": 8,
                "projects": [
                    {"project_id": "165", "name": "Paradise apartments", "status": "active"}
                ]
            }
        }


class ProjectSelectionResult(BaseModel):
    """Result of project selection from user query"""
    project_id: str
    project_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    needs_clarification: bool = False
    clarification_message: Optional[str] = None
    alternative_projects: List[Dict[str, str]] = Field(default_factory=list)
