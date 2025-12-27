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
    """Chat request model - Client sends only query, session_id, and company_id"""

    query: str = Field(..., description="Natural language query", min_length=1)
    company_id: str = Field(..., description="Company ID for context")
    session_id: str = Field(..., description="Session ID for chat history")
    project_id: Optional[str] = Field(
        None, 
        description="Optional project ID (if not provided, LLM will auto-detect from query)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me all outstanding supplier payments for Paradise apartments",
                "company_id": "88",
                "session_id": "user-123-session-456",
                "project_id": None,
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
    Main chat endpoint that processes user queries with full agentic workflow.

    ## Client Payload:
    - **query**: Natural language question
    - **session_id**: Session ID for chat history
    - **company_id**: Company identifier
    - **project_id**: Optional (auto-detected if not provided)

    ## How it works:

    1. **Fetch Projects**: LLM calls Bootstrap API to get all projects for the company

    2. **Project Selection**: If no project_id is provided, the AI analyzes your query
       to determine which project you're asking about. It looks for:
       - Direct project name mentions (e.g., "Paradise apartments")
       - Keywords associated with projects
       - Context clues from chat history

    3. **API Selection**: AI selects the most relevant ERP APIs based on your question

    4. **Data Fetching**: Calls the selected APIs with the determined project context

    5. **Response Generation**: Interprets the data and provides a natural language answer

    ## Example queries:
    - "Show me all outstanding supplier payments for Paradise apartments"
    - "What's the total pending amount for contractors in Elanza project?"
    - "List all overdue invoices" (will ask which project if ambiguous)
    
    ## Response:
    - Returns natural language response with:
      - Selected project information
      - APIs called
      - Raw data (optional)
      - Clarification requests if needed
    """
    return await controller.process_chat(request)
