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
    """Chat response model with comprehensive result information"""

    success: bool = Field(..., description="Whether the request was successful")
    response: str = Field(..., description="Natural language response to the user's query")
    project: Optional[Dict[str, str]] = Field(None, description="Selected project information (id, name)")
    selected_apis: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="List of ERP APIs that were called to answer the query"
    )
    raw_data: Optional[List[Any]] = Field(
        None,
        description="Raw response data from ERP APIs (optional, for debugging)"
    )
    error: Optional[str] = Field(None, description="Error message if request failed")
    needs_clarification: Optional[bool] = Field(
        None,
        description="True if the AI needs more information to answer the query"
    )
    clarification_message: Optional[str] = Field(
        None,
        description="Message asking the user for clarification"
    )
    alternative_projects: Optional[List[Dict[str, str]]] = Field(
        None,
        description="List of possible projects if project detection was ambiguous"
    )
    processing_time_ms: Optional[float] = Field(
        None,
        description="Time taken to process the request in milliseconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "response": "Here are the outstanding supplier payments for Paradise apartments:\n\n1. Alpha Structures: ₹45,000 (30 days overdue)\n2. Beta Suppliers: ₹28,500 (15 days overdue)\n\nTotal outstanding: ₹73,500",
                "project": {
                    "project_id": "165",
                    "name": "Paradise apartments"
                },
                "selected_apis": [
                    {
                        "id": "get_supplier_payments",
                        "name": "Get Supplier Payment Details"
                    }
                ],
                "needs_clarification": False,
                "processing_time_ms": 2456.78
            }
        }


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Process natural language query",
    tags=["chat"],
    responses={
        200: {
            "description": "Successful response with natural language answer",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "response": "Here are the outstanding supplier payments for Paradise apartments:\n\n1. Alpha Structures: ₹45,000 (30 days overdue)\n2. Beta Suppliers: ₹28,500 (15 days overdue)\n\nTotal outstanding: ₹73,500",
                        "project": {
                            "project_id": "165",
                            "name": "Paradise apartments"
                        },
                        "selected_apis": [
                            {
                                "id": "get_supplier_payments",
                                "name": "Get Supplier Payment Details"
                            }
                        ],
                        "needs_clarification": False,
                        "processing_time_ms": 2456.78
                    }
                }
            }
        },
        400: {
            "description": "Bad request - invalid input",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "Query cannot be empty"
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - invalid or missing API key",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {"message": "Invalid API key"}
                    }
                }
            }
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {"message": "Rate limit exceeded. Try again later."}
                    }
                }
            }
        }
    }
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
    
    ## Response Fields:
    - **success**: Boolean indicating if the request was successful
    - **response**: Natural language answer to your query
    - **project**: Information about the selected/detected project
    - **selected_apis**: List of ERP APIs that were called
    - **raw_data**: Raw API response data (optional)
    - **needs_clarification**: True if the AI needs more information
    - **clarification_message**: Message asking for clarification
    - **alternative_projects**: List of possible projects if ambiguous
    - **processing_time_ms**: Time taken to process the request in milliseconds
    
    ## Authentication:
    Requires valid API key in the `X-API-Key` header.
    """
    return await controller.process_chat(request)
