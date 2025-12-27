"""
Chat controller - Handles natural language queries.

This controller orchestrates:
1. Project selection (using LLM)
2. API selection (using LLM)
3. API execution
4. Response interpretation (using LLM)
"""

import time
from typing import Dict, Any
from fastapi import HTTPException
from services.agent_service import AgentService
from services.chat_history_service import chat_history_service
import logging

logger = logging.getLogger(__name__)

# Singleton agent service
_agent_service = None


def get_agent_service() -> AgentService:
    """Get or create agent service instance"""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service


class ChatController:
    """Controller for chat/query processing"""

    async def process_chat(self, request) -> Dict[str, Any]:
        """
        Process a natural language query with full agentic workflow.

        ## Project Selection Logic (How we select the appropriate project):

        1. **LLM fetches projects**: Calls Bootstrap API to get all projects for the company

        2. **If project_id is provided**: Use it directly after validation

        3. **If project_id is NOT provided**: Use LLM to analyze the query
           - The LLM receives the user query + list of available projects
           - It looks for:
             - Direct project name mentions ("Paradise apartments", "Elanza")
             - Partial matches ("Paradise", "SMC")
             - Keywords associated with projects
           - Returns confidence score (0-1)

        4. **Confidence thresholds**:
           - High confidence (>0.7): Use the detected project
           - Medium confidence (0.5-0.7): Use but warn user
           - Low confidence (<0.5): Ask user to clarify

        5. **API Selection & Execution**: 
           - LLM selects relevant APIs based on query
           - Calls APIs with selected project_id
           - Interprets results and generates natural language response

        Args:
            request: ChatRequest with query, company_id, session_id, optional project_id

        Returns:
            ChatResponse with AI-generated answer and metadata
        """
        start_time = time.time()

        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        try:
            agent_service = get_agent_service()

            # 1) Load prior chat history (Mongo + Redis buffer)
            history = await chat_history_service.load_history(
                request.session_id, request.company_id
            )
            
            # 2) Process query through full agentic workflow
            # This will:
            # - Fetch projects from Bootstrap API
            # - Select appropriate project using LLM
            # - Select relevant APIs
            # - Call APIs with project context
            # - Interpret results
            result = await agent_service.process_query(
                user_query=request.query,
                company_id=request.company_id,
                project_id=request.project_id  # Optional, can be None
            )

            # 3) Buffer the exchange in Redis (write-behind to Mongo)
            await chat_history_service.append_exchange(
                request.session_id,
                request.company_id,
                request.query,
                result.get("response", "")
            )

            processing_time = (time.time() - start_time) * 1000

            return {
                "success": result.get("success", True),
                "response": result.get("response", ""),
                "project": result.get("project"),
                "selected_apis": result.get("selected_apis"),
                "raw_data": result.get("raw_data"),
                "needs_clarification": result.get("needs_clarification", False),
                "clarification_message": result.get("clarification_message"),
                "alternative_projects": result.get("alternative_projects"),
                "processing_time_ms": round(processing_time, 2),
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Error processing query: {str(e)}"
            )
