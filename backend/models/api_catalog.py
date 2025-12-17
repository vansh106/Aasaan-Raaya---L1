from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum


class HTTPMethod(str, Enum):
    """HTTP methods supported"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class ParameterType(str, Enum):
    """Parameter types"""

    QUERY = "query"
    PATH = "path"
    FORM = "form"
    BODY = "body"


class APIParameter(BaseModel):
    """API parameter definition"""

    name: str
    type: ParameterType
    description: str
    required: bool = True
    default: Optional[Any] = None
    example: Optional[Any] = None


class APIDefinition(BaseModel):
    """Complete API definition for the catalog"""

    id: str = Field(..., description="Unique identifier for the API")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(
        ..., description="Detailed description of what this API does"
    )
    endpoint: str = Field(..., description="API endpoint path")
    method: HTTPMethod = Field(..., description="HTTP method")
    parameters: List[APIParameter] = Field(
        default_factory=list, description="API parameters"
    )
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    examples: List[str] = Field(default_factory=list, description="Example use cases")
    response_description: str = Field(
        ..., description="Description of response data structure"
    )


class APICatalog(BaseModel):
    """Catalog of all available APIs"""

    apis: List[APIDefinition] = Field(default_factory=list)

    def get_api_by_id(self, api_id: str) -> Optional[APIDefinition]:
        """Get API definition by ID"""
        for api in self.apis:
            if api.id == api_id:
                return api
        return None

    def search_apis(self, query: str) -> List[APIDefinition]:
        """Simple text search across API definitions"""
        query_lower = query.lower()
        results = []
        for api in self.apis:
            if (
                query_lower in api.name.lower()
                or query_lower in api.description.lower()
                or any(query_lower in tag.lower() for tag in api.tags)
            ):
                results.append(api)
        return results
