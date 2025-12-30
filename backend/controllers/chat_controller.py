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
from services.session_context_service import session_context_service
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

            # 1) Load prior chat history (Mongo + Redis buffer) for context retention
            t1 = time.time()
            history = await chat_history_service.load_history(
                request.session_id, request.company_id
            )
            
            # 2) Check session context for stored project (if not explicitly provided)
            project_id = request.project_id
            if not project_id:
                stored_project = await session_context_service.get_project(request.session_id)
                if stored_project:
                    project_id = stored_project.get("project_id")
                    logger.info(f"Using stored project from session: {stored_project.get('project_name')}")
            t2 = time.time()
            
            # 3) Process query through full agentic workflow WITH conversation history
            # This will:
            # - Fetch projects from Bootstrap API
            # - Select appropriate project using LLM (with conversation context)
            # - Select relevant APIs (with conversation context)
            # - Call APIs with project context
            # - Interpret results (with conversation context)
            t3 = time.time()
            result = await agent_service.process_query(
                user_query=request.query,
                company_id=request.company_id,
                project_id=project_id,  # Use stored project if available
                conversation_history=history  # Pass full conversation history for context retention
            )
            t4 = time.time()

            # 4) Store project in session context if successfully selected
            if result.get("success") and result.get("project"):
                project_info = result["project"]
                if project_info.get("id") and project_info.get("name"):
                    await session_context_service.set_project(
                        request.session_id,
                        project_info["id"],
                        project_info["name"]
                    )
                    logger.info(f"Stored project in session context: {project_info['name']}")

            # 5) Buffer the exchange in Redis (write-behind to Mongo)
            await chat_history_service.append_exchange(
                request.session_id,
                request.company_id,
                request.query,
                result.get("response", "")
            )

            processing_time = (time.time() - start_time) * 1000
            
            # Calculate timings
            context_time = round((t2 - t1) * 1000, 2)
            agent_time = round((t4 - t3) * 1000, 2)
            total_time = round(processing_time, 2)
            
            # Get detailed timings from agent service
            agent_timings = result.get("timings", {})
            llm_api_select = agent_timings.get("llm_api_selection_ms", 0)
            llm_project_select = agent_timings.get("llm_project_selection_ms", 0)
            api_calls = agent_timings.get("api_calls_ms", 0)
            llm_interpret = agent_timings.get("llm_interpretation_ms", 0)
            llm_total = llm_api_select + llm_project_select + llm_interpret
            
            # Print detailed timing visualization
            print("\n" + "="*70)
            print("⏱️  PERFORMANCE METRICS - /chat endpoint")
            print("="*70)
            print(f"📦 Context Fetching:        {context_time:>10} ms")
            print("-"*70)
            print(f"🤖 LLM - API Selection:     {llm_api_select:>10} ms")
            print(f"🤖 LLM - Project Selection: {llm_project_select:>10} ms")
            print(f"🔌 External API Calls:      {api_calls:>10} ms")
            print(f"🤖 LLM - Interpretation:    {llm_interpret:>10} ms")
            print("-"*70)
            print(f"🧠 Total LLM Time:          {llm_total:>10} ms")
            print(f"🚀 Agent Processing:        {agent_time:>10} ms")
            print(f"⏱️  TOTAL TIME:              {total_time:>10} ms")
            print("="*70 + "\n")

            return {
                "success": result.get("success", True),
                "response": result.get("response", ""),
                "project": result.get("project"),
                "selected_apis": result.get("selected_apis"),
                "raw_data": result.get("raw_data"),
                "needs_clarification": result.get("needs_clarification", False),
                "clarification_message": result.get("clarification_message"),
                "alternative_projects": result.get("alternative_projects"),
                "processing_time_ms": total_time,
                "timings": {
                    "context_fetching_ms": context_time,
                    "llm_api_selection_ms": llm_api_select,
                    "llm_project_selection_ms": llm_project_select,
                    "api_calls_ms": api_calls,
                    "llm_interpretation_ms": llm_interpret,
                    "llm_total_ms": llm_total,
                    "agent_processing_ms": agent_time,
                    "total_ms": total_time
                }
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Error processing query: {str(e)}"
            )
