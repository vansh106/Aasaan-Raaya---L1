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
        Process a natural language query.

        ## Project Selection Logic (How we select the appropriate project):

        1. **If project_id is provided**: Use it directly after validation

        2. **If project_id is NOT provided**: Use LLM to analyze the query
           - The LLM receives the user query + list of available projects
           - It looks for:
             - Direct project name mentions ("Paradise apartments", "Elanza")
             - Partial matches ("Paradise", "SMC")
             - Keywords associated with projects
           - Returns confidence score (0-1)

        3. **Confidence thresholds**:
           - High confidence (>0.7): Use the detected project
           - Medium confidence (0.5-0.7): Use but warn user
           - Low confidence (<0.5): Ask user to clarify

        4. **Fallback**: If no project detected and only one project exists, use it

        Args:
            request: ChatRequest with query, company_id, optional project_id

        Returns:
            ChatResponse with AI-generated answer
        """
        start_time = time.time()

        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        try:
            agent_service = get_agent_service()

            # Process the query through the agent
            result = await agent_service.process_query(
                request.query, request.company_id, request.project_id
            )

            processing_time = (time.time() - start_time) * 1000

            # Build response
            response = {
                "success": result.get("success", False),
                "response": result.get("response", ""),
                "project": result.get("project"),
                "selected_apis": result.get("selected_apis"),
                "raw_data": result.get("raw_data"),
                "error": result.get("error"),
                "needs_clarification": result.get("needs_clarification"),
                "processing_time_ms": round(processing_time, 2),
            }

            # Add clarification info if needed
            if result.get("needs_clarification"):
                response["clarification_message"] = result.get(
                    "clarification_message", result.get("response")
                )
                response["alternative_projects"] = result.get("alternative_projects")

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Error processing query: {str(e)}"
            )
