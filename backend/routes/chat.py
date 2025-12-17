"""
Chat and query routes.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from controllers.chat_controller import ChatController
from middleware.auth import check_rate_limit

router = APIRouter()
controller = ChatController()


class ChatRequest(BaseModel):
    """Chat request model"""

    query: str = Field(..., description="Natural language query", min_length=1)
    company_id: str = Field(..., description="Company ID for context")
    project_id: Optional[str] = Field(
        None, description="Optional project ID (auto-detected if not provided)"
    )
    context: Optional[List[Dict[str, str]]] = Field(
        None, description="Optional conversation context"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me all outstanding supplier payments for Paradise apartments",
                "company_id": "88",
                "project_id": None,
                "context": None,
            }
        }


class ChatResponse(BaseModel):
    """Chat response model"""

    success: bool
    response: str
    project: Optional[Dict[str, str]] = Field(None, description="Selected project info")
    selected_apis: Optional[List[Dict[str, Any]]] = None
    raw_data: Optional[List[Any]] = None
    error: Optional[str] = None
    needs_clarification: Optional[bool] = None
    clarification_message: Optional[str] = None
    alternative_projects: Optional[List[Dict[str, str]]] = None
    processing_time_ms: Optional[float] = None


@router.post(
    "/chat", response_model=ChatResponse, summary="Process natural language query"
)
async def chat(request: ChatRequest, api_key: str = Depends(check_rate_limit)):
    """
    Main chat endpoint that processes user queries.

    ## How it works:

    1. **Project Selection**: If no project_id is provided, the AI analyzes your query
       to determine which project you're asking about. It looks for:
       - Direct project name mentions (e.g., "Paradise apartments")
       - Keywords associated with projects
       - Context clues

    2. **API Selection**: AI selects the most relevant ERP APIs based on your question

    3. **Data Fetching**: Calls the selected APIs with the determined project context

    4. **Response Generation**: Interprets the data and provides a natural language answer

    ## Example queries:
    - "Show me all outstanding supplier payments for Paradise apartments"
    - "What's the total pending amount for contractors in Elanza project?"
    - "List all overdue invoices" (will ask which project if ambiguous)
    """
    return await controller.process_chat(request)
