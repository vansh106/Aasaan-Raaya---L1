"""
LiteLLM Service - Unified LLM interface supporting multiple providers.

Supports: OpenAI, Gemini, Anthropic, Azure, and many more.
Configure via environment variables:
- LLM_MODEL: Model identifier (e.g., "gpt-4", "gemini/gemini-2.0-flash", "claude-3-opus")
- LLM_API_KEY: API key for the provider
"""

import litellm
from litellm import acompletion
from typing import List, Dict, Any, Optional
import json
from config import settings
import logging
from functools import lru_cache
import hashlib
import time

logger = logging.getLogger(__name__)

# Configure LiteLLM
litellm.set_verbose = settings.debug


class LLMCache:
    """Simple in-memory cache for LLM responses"""
    
    def __init__(self, ttl: int = 300):
        self.cache: Dict[str, tuple[Any, float]] = {}
        self.ttl = ttl
    
    def _hash_key(self, messages: List[Dict], model: str) -> str:
        """Create a hash key for the cache"""
        content = json.dumps(messages, sort_keys=True) + model
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, messages: List[Dict], model: str) -> Optional[str]:
        """Get cached response if exists and not expired"""
        key = self._hash_key(messages, model)
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, messages: List[Dict], model: str, response: str):
        """Cache a response"""
        key = self._hash_key(messages, model)
        self.cache[key] = (response, time.time())
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()


class LLMService:
    """
    Unified LLM service using LiteLLM for multi-provider support.
    
    Features:
    - Support for multiple LLM providers (OpenAI, Gemini, Anthropic, etc.)
    - Response caching for latency optimization
    - Async operations
    - Structured output parsing
    """
    
    def __init__(self):
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.timeout = settings.llm_timeout
        
        # Configure API key based on model provider
        self._configure_api_key()
        
        # Initialize cache
        self.cache = LLMCache(ttl=settings.cache_ttl) if settings.enable_cache else None
        
        logger.info(f"LLM Service initialized with model: {self.model}")
    
    def _configure_api_key(self):
        """Configure API key for the selected provider"""
        api_key = settings.llm_api_key
        
        # LiteLLM automatically uses environment variables, but we can set explicitly
        if "gemini" in self.model.lower():
            litellm.api_key = api_key  # For Gemini via LiteLLM
        elif "claude" in self.model.lower():
            litellm.anthropic_key = api_key
        elif "gpt" in self.model.lower() or "openai" in self.model.lower():
            litellm.openai_key = api_key
        else:
            # Default: set as generic API key
            litellm.api_key = api_key
    
    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        use_cache: bool = True
    ) -> str:
        """
        Make an async LLM call with optional caching.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            use_cache: Whether to use response caching
        
        Returns:
            LLM response text
        """
        # Check cache
        if use_cache and self.cache:
            cached = self.cache.get(messages, self.model)
            if cached:
                logger.debug("Cache hit for LLM request")
                return cached
        
        try:
            response = await acompletion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            
            result = response.choices[0].message.content.strip()
            
            # Cache the response
            if use_cache and self.cache:
                self.cache.set(messages, self.model, result)
            
            return result
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks"""
        text = response_text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        return json.loads(text.strip())
    
    async def select_apis(
        self,
        user_query: str,
        available_apis: List[Dict[str, Any]],
        company_id: str,
        project_id: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Select the most relevant APIs for a user query.
        
        Args:
            user_query: The user's question
            available_apis: List of API definitions from catalog
            company_id: Company ID for context
            project_id: Selected project ID
            conversation_history: Previous conversation for context retention
        
        Returns:
            Dictionary containing selected APIs and parameters
        """
        api_descriptions = "\n\n".join([
            f"API ID: {api['id']}\n"
            f"Name: {api['name']}\n"
            f"Description: {api['description']}\n"
            f"Parameters: {json.dumps(api['parameters'], indent=2)}\n"
            f"Example queries: {', '.join(api['examples'])}"
            for api in available_apis
        ])
        
        system_prompt = """You are an intelligent API selection agent. Based on the user's query and conversation history, you need to:
1. Determine if the query requires API calls or is a general conversational query
2. If APIs are needed, select the most relevant API(s)
3. Extract or infer the required parameter values from the query
4. Use conversation context to understand references and maintain continuity
5. Return a structured JSON response

CRITICAL INSTRUCTIONS:
- Analyze the user query carefully along with previous conversation context
- If the query is general/conversational (e.g., "What is 8 × 8?", "Hello", "Explain something"), set is_general_query to true
- Only select APIs if the query actually needs data from the system
- For each API selected, provide the parameter values
- Use the provided projectId and company_id values (they may be "TBD" if not yet determined)
- If project info was discussed previously, use that context
- Return ONLY valid JSON, no additional text

EXAMPLES OF GENERAL QUERIES (no APIs needed):
- "What is 8 × 8?"
- "Hello"
- "How are you?"
- "Explain what a booking means"
- "What can you help me with?"

EXAMPLES OF API QUERIES (APIs needed):
- "Show me units"
- "What are the bookings?"
- "Total revenue"
- "List all projects" """

        user_prompt = f"""User Query: "{user_query}"

Context:
- Company ID: {company_id}
- Project ID: {project_id}

Available APIs:
{api_descriptions}

Return format (ONLY JSON):
{{
  "is_general_query": false,
  "selected_apis": [
    {{
      "api_id": "api_identifier",
      "confidence": 0.95,
      "reasoning": "why this API was selected",
      "parameters": {{
        "projectId": "{project_id}",
        "company_id": "{company_id}",
        "other_param": "value"
      }}
    }}
  ],
  "needs_clarification": false,
  "clarification_message": ""
}}

If the query is general/conversational (like "What is 8 × 8?"):
{{
  "is_general_query": true,
  "selected_apis": [],
  "needs_clarification": false,
  "clarification_message": ""
}}"""

        # Build messages with conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (but limit to last 10 messages to avoid token limits)
        if conversation_history:
            recent_history = conversation_history[-10:]
            messages.extend(recent_history)
        
        # Add current query
        messages.append({"role": "user", "content": user_prompt})
        
        try:
            response_text = await self._call_llm(messages)
            result = self._parse_json_response(response_text)
            # Ensure is_general_query exists in response
            if "is_general_query" not in result:
                result["is_general_query"] = False
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {
                "is_general_query": False,
                "selected_apis": [],
                "needs_clarification": True,
                "clarification_message": "I had trouble understanding which API to use. Could you rephrase your question?"
            }
        except Exception as e:
            logger.error(f"Error in API selection: {e}")
            return {
                "is_general_query": False,
                "selected_apis": [],
                "needs_clarification": True,
                "clarification_message": f"An error occurred: {str(e)}"
            }
    
    async def select_project(
        self,
        user_query: str,
        projects: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Select the most appropriate project based on user query.
        
        Args:
            user_query: The user's question
            projects: List of available projects
            conversation_history: Previous conversation for context retention
        
        Returns:
            Dictionary with selected project info
        """
        if not projects:
            return {
                "selected_project": None,
                "confidence": 0.0,
                "needs_clarification": True,
                "clarification_message": "No projects available. Please initialize the company first."
            }
        
        if len(projects) == 1:
            # Only one project, use it directly
            return {
                "selected_project": {
                    "project_id": projects[0]["project_id"],
                    "project_name": projects[0]["name"]
                },
                "confidence": 1.0,
                "needs_clarification": False,
                "reasoning": "Only one project available"
            }
        
        project_list = "\n".join([
            f"- ID: {p['project_id']}, Name: {p['name']}, "
            f"Location: {p.get('location', 'N/A')}, "
            f"Keywords: {', '.join(p.get('keywords', []))}"
            for p in projects
        ])
        
        system_prompt = """You are a project selection assistant. Analyze the user query and conversation history to select the most relevant project.

CRITICAL RULES:
- Review conversation history to see if a project was already mentioned or selected
- If a project was discussed earlier in the conversation, use that context with HIGH confidence
- If the current query doesn't mention a specific project but one was discussed before, ALWAYS use the previous project
- If only one project is available, use it directly
- Only set needs_clarification=true if NO project has EVER been mentioned in the conversation AND there are multiple projects available
- Avoid asking for project clarification unnecessarily - use context from previous messages
- Return ONLY valid JSON."""

        user_prompt = f"""User Query: "{user_query}"

Available Projects:
{project_list}

Analyze if the query mentions or implies a specific project, or if a project was discussed in previous messages. Return JSON:
{{
  "selected_project": {{
    "project_id": "id",
    "project_name": "name"
  }} or null,
  "confidence": 0.0 to 1.0,
  "reasoning": "why this project was selected",
  "needs_clarification": true/false,
  "clarification_message": "message asking user to specify project" (if needs_clarification is true),
  "alternative_projects": [list of possible project names if multiple match]
}}"""

        # Build messages with conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (limit to last 10 messages)
        if conversation_history:
            recent_history = conversation_history[-10:]
            messages.extend(recent_history)
        
        # Add current query
        messages.append({"role": "user", "content": user_prompt})
        
        try:
            response_text = await self._call_llm(messages, use_cache=False)
            return self._parse_json_response(response_text)
        except Exception as e:
            logger.error(f"Error in project selection: {e}")
            # Fallback: return first project with low confidence
            return {
                "selected_project": {
                    "project_id": projects[0]["project_id"],
                    "project_name": projects[0]["name"]
                },
                "confidence": 0.3,
                "needs_clarification": True,
                "clarification_message": f"I'm not sure which project you're referring to. Available projects: {', '.join(p['name'] for p in projects)}"
            }
    
    async def interpret_data(
        self,
        user_query: str,
        api_responses: List[Dict[str, Any]],
        project_name: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Interpret API response data and provide a natural language answer.
        
        Args:
            user_query: The original user question
            api_responses: List of API responses with data
            project_name: Name of the selected project for context
            conversation_history: Previous conversation for context retention
        
        Returns:
            Natural language interpretation of the data
        """
        formatted_responses = "\n\n".join([
            f"API: {resp['api_name']}\n"
            f"Endpoint: {resp['endpoint']}\n"
            f"Data: {json.dumps(resp.get('data', resp.get('error')), indent=2)}"
            for resp in api_responses
        ])
        
        context = f"Project: {project_name}\n" if project_name else ""
        
        system_prompt = """You are a helpful assistant that interprets API data to answer user questions.

FORMATTING INSTRUCTIONS:
- Use clean, professional markdown formatting
- For lists of items, use TABLES instead of bullet points when showing multiple data fields
- Use headers (##, ###) to organize sections
- Format currency with ₹ symbol and proper commas (e.g., ₹15,765,325.60)
- Use bold sparingly, only for key totals or important highlights

CONTENT INSTRUCTIONS:
- Analyze the API response data carefully
- Provide a clear, concise answer to the user's question
- Include relevant calculations or summaries for numerical data
- Be conversational and professional
- Use conversation history to understand context and references
- Start with a brief summary, then provide details
- Avoid repeating information already provided in the conversation"""

        user_prompt = f"""User's Question: "{user_query}"

{context}
API Response Data:
{formatted_responses}

Please provide a clear, well-formatted response."""

        # Build messages with conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (limit to last 10 messages for context)
        if conversation_history:
            recent_history = conversation_history[-10:]
            messages.extend(recent_history)
        
        # Add current query and data
        messages.append({"role": "user", "content": user_prompt})
        
        try:
            return await self._call_llm(messages, use_cache=False)
        except Exception as e:
            logger.error(f"Error in data interpretation: {e}")
            return f"I received the data but had trouble interpreting it: {str(e)}"
    
    async def chat(
        self,
        message: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Simple chat interface.
        
        Args:
            message: User message
            context: Optional conversation history
        
        Returns:
            LLM response
        """
        messages = context.copy() if context else []
        messages.append({"role": "user", "content": message})
        
        try:
            return await self._call_llm(messages)
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def clear_cache(self):
        """Clear the response cache"""
        if self.cache:
            self.cache.clear()
            logger.info("LLM cache cleared")

