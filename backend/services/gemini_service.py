import google.generativeai as genai
from typing import List, Dict, Any, Optional
import json
from config import settings


class GeminiService:
    """Service for interacting with Google Gemini API"""

    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    async def select_apis(
        self, user_query: str, available_apis: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use Gemini to select the most relevant APIs for the user query

        Args:
            user_query: The user's question
            available_apis: List of API definitions from catalog

        Returns:
            Dictionary containing selected APIs and parameter values
        """

        # Create a prompt for API selection
        api_descriptions = "\n\n".join(
            [
                f"API ID: {api['id']}\n"
                f"Name: {api['name']}\n"
                f"Description: {api['description']}\n"
                f"Parameters: {json.dumps(api['parameters'], indent=2)}\n"
                f"Example queries: {', '.join(api['examples'])}"
                for api in available_apis
            ]
        )

        prompt = f"""You are an intelligent API selection agent. Based on the user's query, you need to:
1. Select the most relevant API(s) that can answer the query
2. Extract or infer the required parameter values from the query
3. Return a structured JSON response

User Query: "{user_query}"

Available APIs:
{api_descriptions}

CRITICAL INSTRUCTIONS:
- Analyze the user query carefully
- Select one or more APIs that are relevant
- For each API, provide the parameter values
- ALWAYS use default values or examples from the parameter definitions if values are not in the query
- NEVER set "needs_clarification" to true - always proceed with defaults
- For projectId use "165", for company_id use "88", for user_id use "4" as defaults
- For supplierId use "-1" (all suppliers) as default
- For supplierType use "Contract work" as default
- Return ONLY valid JSON, no additional text

Return format (ONLY JSON):
{{
  "selected_apis": [
    {{
      "api_id": "api_identifier",
      "confidence": 0.95,
      "reasoning": "why this API was selected",
      "parameters": {{
        "param_name": "value"
      }}
    }}
  ],
  "needs_clarification": false,
  "clarification_message": ""
}}

Response:"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Clean up response if it has markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            result = json.loads(response_text)
            return result

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response text: {response_text}")
            return {
                "selected_apis": [],
                "needs_clarification": True,
                "clarification_message": "I had trouble understanding which API to use. Could you rephrase your question?",
            }
        except Exception as e:
            print(f"Error in API selection: {e}")
            return {
                "selected_apis": [],
                "needs_clarification": True,
                "clarification_message": f"An error occurred: {str(e)}",
            }

    async def interpret_data(
        self, user_query: str, api_responses: List[Dict[str, Any]]
    ) -> str:
        """
        Use Gemini to interpret API response data and provide a natural language answer

        Args:
            user_query: The original user question
            api_responses: List of API responses with data

        Returns:
            Natural language interpretation of the data
        """

        # Format API responses for the prompt
        formatted_responses = "\n\n".join(
            [
                f"API: {resp['api_name']}\n"
                f"Endpoint: {resp['endpoint']}\n"
                f"Data: {json.dumps(resp['data'], indent=2)}"
                for resp in api_responses
            ]
        )

        prompt = f"""You are a helpful assistant that interprets API data to answer user questions.

User's Question: "{user_query}"

API Response Data:
{formatted_responses}

FORMATTING INSTRUCTIONS:
- Use clean, professional markdown formatting
- For lists of items, use TABLES instead of bullet points when showing multiple data fields
- Use headers (##, ###) to organize sections
- Minimize use of asterisks (*) - use them only for true emphasis
- Format currency with ₹ symbol and proper commas (e.g., ₹15,765,325.60)
- Use bold (**text**) sparingly, only for key totals or important highlights
- Use line breaks between sections for readability

CONTENT INSTRUCTIONS:
- Analyze the API response data carefully
- Provide a clear, concise answer to the user's question
- Include relevant calculations or summaries for numerical data
- Summarize key insights from the data
- Be conversational and professional
- Start with a brief summary, then provide details

EXAMPLE FORMAT:
## Summary
Brief overview with key totals.

## Detailed Breakdown
| Supplier | Invoice No. | Due Date | Balance | Status |
|----------|-------------|----------|---------|--------|
| Name     | 123         | DD/MM/YY | ₹X,XXX  | Overdue|

## Key Insights
- Insight 1
- Insight 2

Your response:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in data interpretation: {e}")
            return f"I received the data but had trouble interpreting it: {str(e)}"

    async def chat(
        self, message: str, context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Simple chat interface with Gemini

        Args:
            message: User message
            context: Optional conversation history

        Returns:
            Gemini's response
        """
        try:
            if context:
                # Build conversation context
                conversation = "\n".join(
                    [f"{msg['role']}: {msg['content']}" for msg in context]
                )
                full_prompt = f"{conversation}\nUser: {message}\nAssistant:"
            else:
                full_prompt = message

            response = self.model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in chat: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
