"""
Database Service - MongoDB operations for company, project, supplier, and module management.

Uses Motor for async MongoDB operations with connection pooling.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from config import settings
from models.company import Company, Project, Supplier, Module
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    MongoDB database service for company and project management.
    Uses Motor for async MongoDB operations.
    """

    _instance: Optional["DatabaseService"] = None
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None

    def __new__(cls):
        """Singleton pattern for database connection"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self):
        """Initialize database connection"""
        if self._client is None:
            self._client = AsyncIOMotorClient(
                settings.mongodb_uri, serverSelectionTimeoutMS=5000
            )
            self._db = self._client[settings.mongodb_database]

            # Create indexes
            await self._create_indexes()
            logger.info(f"Connected to MongoDB: {settings.mongodb_database}")

    async def disconnect(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("Disconnected from MongoDB")

    async def _create_indexes(self):
        """Create necessary database indexes for performance"""
        # Company collection indexes
        await self._db.companies.create_index("company_id", unique=True)
        await self._db.companies.create_index("name")
        await self._db.companies.create_index("projects.project_id")
        await self._db.companies.create_index("projects.name")
        await self._db.companies.create_index("suppliers.supplier_id")
        await self._db.companies.create_index("suppliers.name")
        await self._db.companies.create_index("suppliers.type")

        # Chat sessions indexes
        await self._db.chat_sessions.create_index("session_id", unique=True)
        await self._db.chat_sessions.create_index(
            "last_activity", expireAfterSeconds=settings.chat_session_ttl_seconds
        )

        logger.info("Database indexes created")

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if self._db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._db

    # ==================== Company Operations ====================

    async def get_company(self, company_id: str) -> Optional[Company]:
        """Get company by company_id"""
        doc = await self.db.companies.find_one({"company_id": company_id})
        if doc:
            doc.pop("_id", None)  # Remove MongoDB _id field
            return Company(**doc)
        return None

    async def create_company(self, company: Company) -> bool:
        """Create a new company"""
        try:
            doc = company.model_dump()
            doc["created_at"] = datetime.utcnow()
            doc["updated_at"] = datetime.utcnow()
            await self.db.companies.insert_one(doc)
            logger.info(f"Created company: {company.company_id}")
            return True
        except DuplicateKeyError:
            logger.warning(f"Company already exists: {company.company_id}")
            return False
        except Exception as e:
            logger.error(f"Error creating company: {e}")
            raise

    async def update_company(self, company: Company) -> bool:
        """Update an existing company"""
        try:
            doc = company.model_dump()
            doc["updated_at"] = datetime.utcnow()

            result = await self.db.companies.update_one(
                {"company_id": company.company_id}, {"$set": doc}
            )

            if result.modified_count > 0:
                logger.info(f"Updated company: {company.company_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating company: {e}")
            raise

    async def upsert_company(self, company: Company) -> bool:
        """Create or update company"""
        try:
            doc = company.model_dump()
            doc["updated_at"] = datetime.utcnow()

            result = await self.db.companies.update_one(
                {"company_id": company.company_id},
                {"$set": doc, "$setOnInsert": {"created_at": datetime.utcnow()}},
                upsert=True,
            )

            action = "Created" if result.upserted_id else "Updated"
            logger.info(f"{action} company: {company.company_id}")
            return True
        except Exception as e:
            logger.error(f"Error upserting company: {e}")
            raise

    async def delete_company(self, company_id: str) -> bool:
        """Delete a company"""
        result = await self.db.companies.delete_one({"company_id": company_id})
        if result.deleted_count > 0:
            logger.info(f"Deleted company: {company_id}")
            return True
        return False

    async def list_companies(self) -> List[Company]:
        """List all companies"""
        companies = []
        async for doc in self.db.companies.find():
            doc.pop("_id", None)
            companies.append(Company(**doc))
        return companies

    # ==================== Project Operations ====================

    async def get_project(self, company_id: str, project_id: str) -> Optional[Project]:
        """Get a specific project from a company"""
        company = await self.get_company(company_id)
        if company:
            return company.get_project_by_id(project_id)
        return None

    async def add_project(self, company_id: str, project: Project) -> bool:
        """Add a project to a company"""
        try:
            result = await self.db.companies.update_one(
                {"company_id": company_id},
                {
                    "$push": {"projects": project.model_dump()},
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error adding project: {e}")
            raise

    async def update_projects(self, company_id: str, projects: List[Project]) -> bool:
        """Replace all projects for a company (used during sync)"""
        try:
            result = await self.db.companies.update_one(
                {"company_id": company_id},
                {
                    "$set": {
                        "projects": [p.model_dump() for p in projects],
                        "updated_at": datetime.utcnow(),
                        "last_synced_at": datetime.utcnow(),
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating projects: {e}")
            raise

    async def search_projects(self, company_id: str, query: str) -> List[Project]:
        """Search projects by name, keywords, or aliases"""
        company = await self.get_company(company_id)
        if company:
            return company.search_projects(query)
        return []

    async def get_default_project(self, company_id: str) -> Optional[Project]:
        """Get the default project for a company"""
        company = await self.get_company(company_id)
        if company and company.default_project_id:
            return company.get_project_by_id(company.default_project_id)
        # If no default, return first active project
        if company and company.projects:
            for project in company.projects:
                if project.status.value == "active":
                    return project
            return company.projects[0]
        return None

    async def set_default_project(self, company_id: str, project_id: str) -> bool:
        """Set the default project for a company"""
        try:
            result = await self.db.companies.update_one(
                {"company_id": company_id},
                {
                    "$set": {
                        "default_project_id": project_id,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error setting default project: {e}")
            raise

    # ==================== Supplier Operations ====================

    async def get_suppliers(
        self, company_id: str, supplier_type: Optional[str] = None
    ) -> List[Supplier]:
        """Get suppliers for a company, optionally filtered by type"""
        company = await self.get_company(company_id)
        if not company:
            return []

        suppliers = company.suppliers
        if supplier_type:
            suppliers = [
                s for s in suppliers if s.type and s.type.value == supplier_type
            ]

        return suppliers

    async def get_supplier(
        self, company_id: str, supplier_id: str
    ) -> Optional[Supplier]:
        """Get a specific supplier"""
        company = await self.get_company(company_id)
        if company:
            return company.get_supplier_by_id(supplier_id)
        return None

    async def update_suppliers(
        self, company_id: str, suppliers: List[Supplier]
    ) -> bool:
        """Replace all suppliers for a company"""
        try:
            result = await self.db.companies.update_one(
                {"company_id": company_id},
                {
                    "$set": {
                        "suppliers": [s.model_dump() for s in suppliers],
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating suppliers: {e}")
            raise

    # ==================== Module Operations ====================

    async def get_modules(self, company_id: str) -> List[Module]:
        """Get all modules for a company"""
        company = await self.get_company(company_id)
        if company:
            return company.modules
        return []

    async def update_modules(self, company_id: str, modules: List[Module]) -> bool:
        """Replace all modules for a company"""
        try:
            result = await self.db.companies.update_one(
                {"company_id": company_id},
                {
                    "$set": {
                        "modules": [m.model_dump() for m in modules],
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating modules: {e}")
            raise

    # ==================== Health Check ====================

    async def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            await self.db.command("ping")
            company_count = await self.db.companies.count_documents({})
            return {
                "status": "healthy",
                "database": settings.mongodb_database,
                "company_count": company_count,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global database instance
db_service = DatabaseService()
