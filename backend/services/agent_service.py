"""
Agent Service - Orchestrates the entire agentic workflow.

Features:
- Automatic project selection from user query using LLM
- API selection and execution
- Data interpretation
- Error handling with user prompts
"""

import time
from typing import Dict, Any, List, Optional
import json
from pathlib import Path
import asyncio
from models.api_catalog import APICatalog, APIDefinition
from services.llm_service import LLMService
from services.api_caller import APICallerService
from services.erp_service import erp_service
from services.database import db_service
from models.company import Company, Project
import logging

logger = logging.getLogger(__name__)


class AgentService:
    """Main agent service that orchestrates the entire workflow"""

    def __init__(self):
        self.llm_service = LLMService()
        self.api_caller = APICallerService()
        self.catalog = self._load_catalog()

        logger.info("Agent service initialized")

    def _load_catalog(self) -> APICatalog:
        """Load API catalog from JSON file"""
        catalog_path = Path(__file__).parent.parent / "data" / "api_catalog.json"

        if catalog_path.exists():
            with open(catalog_path, "r") as f:
                catalog_data = json.load(f)
                return APICatalog(**catalog_data)
        else:
            # Return empty catalog if file doesn't exist
            return APICatalog(apis=[])

    async def _select_project(
        self, user_query: str, company_id: str, conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Select the appropriate project based on user query and company.

        ## How Project Selection Works:
        
        1. Fetch all projects for the company from ERP Bootstrap API
        2. If only 1 project exists, use it automatically
        3. Otherwise, use LLM to analyze the query and match to a project
        4. LLM looks for:
           - Direct project name mentions ("Paradise apartments")
           - Partial matches ("Paradise", "SMC")
           - Keywords in project metadata
        5. Returns confidence score (0-1):
           - >0.7: High confidence, use detected project
           - 0.5-0.7: Medium confidence, use but note uncertainty
           - <0.5: Low confidence, ask user to clarify

        Returns dict with:
        - project_id: Selected project ID
        - project_name: Project name
        - needs_clarification: Whether user needs to specify project
        - clarification_message: Message to prompt user
        """
        # Fetch bootstrap data from ERP to get projects
        logger.info(f"Fetching projects from Bootstrap API for company {company_id}")
        bootstrap_response = await erp_service.fetch_bootstrap(company_id)

        if not bootstrap_response.get("success"):
            return {
                "project_id": None,
                "project_name": None,
                "needs_clarification": True,
                "clarification_message": f"Unable to fetch company data: {bootstrap_response.get('error', 'Unknown error')}",
            }

        bootstrap_data = bootstrap_response.get("data", {})
        projects = bootstrap_data.get("projects", [])

        if not projects:
            return {
                "project_id": None,
                "project_name": None,
                "needs_clarification": True,
                "clarification_message": "No projects found for this company. Please sync projects first.",
            }

        # Convert projects to standardized format for LLM
        projects_data = [
            {
                "project_id": str(p.get("id") or p.get("project_id")),
                "name": p.get("name", ""),
                "description": p.get("description", ""),
                "keywords": p.get("keywords", []),
                "aliases": p.get("aliases", []),
                "location": p.get("location", ""),
                "status": p.get("status", "active"),
            }
            for p in projects
        ]

        logger.info(f"Found {len(projects_data)} projects from Bootstrap API")

        # Use LLM to select project (with conversation history for context)
        selection_result = await self.llm_service.select_project(
            user_query, projects_data, conversation_history=conversation_history or []
        )

        confidence = selection_result.get("confidence", 0)

        if selection_result.get("needs_clarification") and confidence < 0.5:
            # Build list of project options for user
            project_options = [
                {"project_id": p["project_id"], "name": p["name"]}
                for p in projects_data
            ]
            return {
                "project_id": None,
                "project_name": None,
                "needs_clarification": True,
                "clarification_message": selection_result.get(
                    "clarification_message",
                    f"Please specify which project you're asking about. Available projects: {', '.join(p['name'] for p in projects_data)}",
                ),
                "alternative_projects": project_options,
            }

        # Check if we have a selected project
        selected = selection_result.get("selected_project")
        if selected:
            return {
                "project_id": selected["project_id"],
                "project_name": selected["project_name"],
                "needs_clarification": False,
                "confidence": confidence,
                "reasoning": selection_result.get("reasoning", ""),
            }

        # Fallback: use first project with medium confidence
        if projects_data:
            return {
                "project_id": projects_data[0]["project_id"],
                "project_name": projects_data[0]["name"],
                "needs_clarification": True,
                "clarification_message": f"Using project: {projects_data[0]['name']}. Please specify if you meant a different project.",
                "confidence": 0.5,
            }

        return {
            "project_id": None,
            "project_name": None,
            "needs_clarification": True,
            "clarification_message": "Unable to determine project. Please specify which project you're asking about.",
        }

    async def process_query(
        self,
        user_query: str,
        company_id: str,
        project_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the complete agentic workflow.

        NEW Flow (Context-Aware):
        1. Use LLM to understand query and select relevant APIs (without requiring project)
        2. If no APIs needed (general query), answer directly via chat
        3. If APIs are needed and require project, THEN select/validate project
        4. Fetch data from selected APIs (in parallel)
        5. Use LLM to interpret the data and generate response

        Args:
            user_query: The user's question
            company_id: Company ID for context
            project_id: Optional project ID (if not provided, will be auto-selected only when needed)
            conversation_history: Optional conversation history for context retention

        Returns:
            Dictionary containing the response and metadata
        """
        # Initialize timing tracker
        timings = {}
        
        try:
            logger.info(f"Processing query: {user_query} for company: {company_id}")

            # Step 1: API Selection (BEFORE project selection)
            # This allows us to determine if we actually need a project
            available_apis = [api.model_dump() for api in self.catalog.apis]

            # Use LLM to select relevant APIs (without requiring project initially)
            # Pass None for project_id to signal we don't have one yet
            t_api_select_start = time.time()
            selection_result = await self.llm_service.select_apis(
                user_query,
                available_apis,
                company_id,
                project_id or "TBD",  # Will be determined later if needed
                conversation_history=conversation_history or []
            )
            t_api_select_end = time.time()
            timings["llm_api_selection_ms"] = round((t_api_select_end - t_api_select_start) * 1000, 2)

            logger.debug(f"API Selection Result: {json.dumps(selection_result, indent=2)}")

            selected_apis = selection_result.get("selected_apis", [])

            # Step 2: Handle queries that don't need APIs (general chat)
            if not selected_apis:
                # Check if this is a general conversational query (like "What is 8 × 8?")
                if selection_result.get("is_general_query"):
                    logger.info("Handling as general conversational query (no API needed)")
                    general_response = await self.llm_service.chat(
                        user_query,
                        context=conversation_history or []
                    )
                    return {
                        "success": True,
                        "response": general_response,
                        "selected_apis": [],
                        "is_general_query": True,
                        "timings": timings,
                    }
                
                # Check if clarification is needed
                if selection_result.get("needs_clarification"):
                    return {
                        "success": False,
                        "response": selection_result.get(
                            "clarification_message",
                            "I couldn't find a relevant API. Could you rephrase your question?",
                        ),
                        "needs_clarification": True,
                        "timings": timings,
                    }
                
                # No APIs found, treat as general query anyway
                logger.info("No APIs selected, falling back to general chat")
                general_response = await self.llm_service.chat(
                    user_query,
                    context=conversation_history or []
                )
                return {
                    "success": True,
                    "response": general_response,
                    "selected_apis": [],
                    "is_general_query": True,
                    "timings": timings,
                }

            # Step 3: Project Selection (ONLY if APIs were selected)
            # Now we know we need APIs, so we need a project
            if project_id:
                # Validate provided project_id
                project = await db_service.get_project(company_id, project_id)
                if not project:
                    return {
                        "success": False,
                        "error": "Invalid project",
                        "response": f"Project {project_id} not found for company {company_id}.",
                        "needs_clarification": True,
                        "timings": timings,
                    }
                project_selection = {
                    "project_id": project_id,
                    "project_name": project.name,
                    "needs_clarification": False,
                }
                timings["llm_project_selection_ms"] = 0
            else:
                # Auto-select project from query using LLM (with conversation history)
                t_project_start = time.time()
                project_selection = await self._select_project(
                    user_query, company_id, conversation_history=conversation_history or []
                )
                t_project_end = time.time()
                timings["llm_project_selection_ms"] = round((t_project_end - t_project_start) * 1000, 2)
                logger.info(f"⏱️ Project selection took: {timings['llm_project_selection_ms']} ms")

            # Check if we need project clarification
            if (
                project_selection.get("needs_clarification")
                and not project_selection.get("project_id")
            ):
                return {
                    "success": False,
                    "error": "Project clarification needed",
                    "response": project_selection.get("clarification_message"),
                    "needs_clarification": True,
                    "alternative_projects": project_selection.get(
                        "alternative_projects", []
                    ),
                    "timings": timings,
                }

            selected_project_id = project_selection["project_id"]
            selected_project_name = project_selection["project_name"]

            logger.info(
                f"Selected project: {selected_project_name} ({selected_project_id})"
            )

            # Step 4: Call the selected APIs (in parallel for latency optimization)
            api_call_tasks = []

            for selected_api in selected_apis:
                api_id = selected_api.get("api_id")
                parameters = selected_api.get("parameters", {})

                # Get API definition from catalog
                api_def = self.catalog.get_api_by_id(api_id)

                if not api_def:
                    logger.warning(f"API {api_id} not found in catalog")
                    continue

                # Ensure project_id and company_id are set
                parameters["projectId"] = parameters.get(
                    "projectId", selected_project_id
                )
                parameters["company_id"] = parameters.get("company_id", company_id)

                # Fill in missing parameters with defaults or examples
                for param in api_def.parameters:
                    if param.name not in parameters:
                        if param.default is not None:
                            parameters[param.name] = param.default
                        elif param.example is not None:
                            parameters[param.name] = param.example

                # Create async task for API call
                api_call_tasks.append(
                    self._call_api_with_metadata(
                        api_def, parameters, selected_api.get("reasoning", "")
                    )
                )

            # Execute all API calls in parallel
            t_api_calls_start = time.time()
            if api_call_tasks:
                api_responses = await asyncio.gather(
                    *api_call_tasks, return_exceptions=True
                )
                # Filter out exceptions
                api_responses = [
                    r for r in api_responses if not isinstance(r, Exception)
                ]
            else:
                api_responses = []
            t_api_calls_end = time.time()
            timings["api_calls_ms"] = round((t_api_calls_end - t_api_calls_start) * 1000, 2)

            if not api_responses:
                return {
                    "success": False,
                    "error": "Failed to fetch data from APIs",
                    "response": "I encountered an error while fetching the data. Please try again.",
                    "selected_apis": selected_apis,
                    "project": {
                        "id": selected_project_id,
                        "name": selected_project_name,
                    },
                    "timings": timings,
                }

            # Step 5: Interpret the data using LLM (with conversation history)
            logger.info("Interpreting data with LLM...")
            t_interpret_start = time.time()
            interpretation = await self.llm_service.interpret_data(
                user_query,
                api_responses,
                selected_project_name,
                conversation_history=conversation_history or []
            )
            t_interpret_end = time.time()
            timings["llm_interpretation_ms"] = round((t_interpret_end - t_interpret_start) * 1000, 2)

            return {
                "success": True,
                "response": interpretation,
                "selected_apis": selected_apis,
                "api_responses": api_responses,
                "raw_data": [
                    resp.get("data") for resp in api_responses if "data" in resp
                ],
                "project": {"id": selected_project_id, "name": selected_project_name},
                "clarification_note": (
                    project_selection.get("clarification_message")
                    if project_selection.get("needs_clarification")
                    else None
                ),
                "timings": timings,
            }

        except Exception as e:
            logger.error(f"Error in process_query: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "response": f"I encountered an error while processing your query: {str(e)}",
                "timings": timings if 'timings' in locals() else {},
            }

    async def _call_api_with_metadata(
        self, api_def: APIDefinition, parameters: Dict[str, Any], reasoning: str
    ) -> Dict[str, Any]:
        """Call API and wrap response with metadata"""
        logger.info(f"Calling API: {api_def.id} with parameters: {parameters}")

        api_response = await self.api_caller.call_api(api_def, parameters)

        if api_response.get("success"):
            return {
                "api_id": api_def.id,
                "api_name": api_def.name,
                "endpoint": api_def.endpoint,
                "data": api_response.get("data"),
                "reasoning": reasoning,
            }
        else:
            return {
                "api_id": api_def.id,
                "api_name": api_def.name,
                "endpoint": api_def.endpoint,
                "error": api_response.get("error"),
                "reasoning": reasoning,
            }

    def get_all_apis(self) -> List[APIDefinition]:
        """Get all available APIs from catalog"""
        return self.catalog.apis

    def add_api_to_catalog(self, api_definition: APIDefinition) -> bool:
        """Add a new API to the catalog"""
        try:
            self.catalog.apis.append(api_definition)

            # Save to file
            catalog_path = Path(__file__).parent.parent / "data" / "api_catalog.json"
            catalog_path.parent.mkdir(parents=True, exist_ok=True)

            with open(catalog_path, "w") as f:
                json.dump(self.catalog.model_dump(), f, indent=2)

            logger.info(f"Added API to catalog: {api_definition.id}")
            return True
        except Exception as e:
            logger.error(f"Error adding API to catalog: {e}")
            return False

    def reload_catalog(self):
        """Reload the API catalog from disk"""
        self.catalog = self._load_catalog()
        logger.info("API catalog reloaded")
