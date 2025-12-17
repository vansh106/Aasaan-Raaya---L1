"""
API Caller Service - Makes HTTP calls to external ERP APIs.

Features:
- Async HTTP operations with httpx
- Connection pooling for latency optimization
- Configurable timeout
- Support for all HTTP methods
"""

import httpx
from typing import Dict, Any, Optional
from config import settings
from models.api_catalog import APIDefinition, HTTPMethod, ParameterType
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class APICallerService:
    """Service for making API calls to the ERP system"""

    def __init__(self):
        self.base_url = settings.erp_base_url
        self.timeout = settings.erp_api_timeout
        
        # Connection pool for better performance
        self._client: Optional[httpx.AsyncClient] = None
        
        logger.info(f"API Caller initialized with base URL: {self.base_url}")

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client with connection pooling"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
                http2=True  # Enable HTTP/2 for better performance
            )
        return self._client

    async def close(self):
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
            logger.info("API Caller client closed")

    def _build_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Build request headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Add any custom headers
        if custom_headers:
            headers.update(custom_headers)
        
        return headers

    async def call_api(
        self,
        api_definition: APIDefinition,
        parameters: Dict[str, Any],
        custom_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make an API call based on the definition and parameters.

        Args:
            api_definition: The API definition from catalog
            parameters: Parameter values to use
            custom_headers: Optional custom headers to include

        Returns:
            Dictionary containing the API response
        """
        try:
            # Build the full URL
            url = f"{self.base_url}{api_definition.endpoint}"

            # Separate parameters by type
            query_params = {}
            form_data = {}
            path_params = {}
            body_data = {}

            for param_name, param_value in parameters.items():
                # Find the parameter definition
                param_def = None
                for p in api_definition.parameters:
                    if p.name == param_name:
                        param_def = p
                        break

                if param_def:
                    if param_def.type == ParameterType.QUERY:
                        query_params[param_name] = param_value
                    elif param_def.type == ParameterType.FORM:
                        form_data[param_name] = param_value
                    elif param_def.type == ParameterType.PATH:
                        path_params[param_name] = param_value
                    elif param_def.type == ParameterType.BODY:
                        body_data[param_name] = param_value
                else:
                    # Default to query parameter if not defined
                    query_params[param_name] = param_value

            # Replace path parameters in URL
            for param_name, param_value in path_params.items():
                url = url.replace(f"{{{param_name}}}", str(param_value))

            # Get HTTP client
            client = await self._get_client()
            headers = self._build_headers(custom_headers)

            logger.debug(f"Calling {api_definition.method.value} {url}")
            logger.debug(f"Query params: {query_params}")

            # Make the HTTP request
            if api_definition.method == HTTPMethod.GET:
                response = await client.get(
                    url, params=query_params, headers=headers
                )
            elif api_definition.method == HTTPMethod.POST:
                if form_data:
                    response = await client.post(
                        url,
                        params=query_params,
                        data=form_data,
                        headers=headers,
                    )
                else:
                    response = await client.post(
                        url,
                        params=query_params,
                        json=body_data if body_data else None,
                        headers=headers,
                    )
            elif api_definition.method == HTTPMethod.PUT:
                response = await client.put(
                    url, params=query_params, json=body_data, headers=headers
                )
            elif api_definition.method == HTTPMethod.PATCH:
                response = await client.patch(
                    url, params=query_params, json=body_data, headers=headers
                )
            elif api_definition.method == HTTPMethod.DELETE:
                response = await client.delete(
                    url, params=query_params, headers=headers
                )
            else:
                return {
                    "success": False,
                    "error": f"Unsupported HTTP method: {api_definition.method}",
                }

            # Check if request was successful
            response.raise_for_status()

            # Parse response
            try:
                data = response.json()
            except Exception:
                data = response.text

            logger.info(f"API call successful: {api_definition.id}")
            
            return {
                "success": True,
                "status_code": response.status_code,
                "data": data,
                "api_id": api_definition.id,
                "api_name": api_definition.name,
                "endpoint": api_definition.endpoint,
            }

        except httpx.TimeoutException:
            logger.error(f"Timeout calling API: {api_definition.id}")
            return {
                "success": False,
                "error": f"Request timeout after {self.timeout} seconds",
                "api_id": api_definition.id,
                "api_name": api_definition.name,
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling API {api_definition.id}: {e}")
            return {
                "success": False,
                "error": f"HTTP error {e.response.status_code}: {str(e)}",
                "status_code": e.response.status_code,
                "api_id": api_definition.id,
                "api_name": api_definition.name,
            }
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling API {api_definition.id}: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {str(e)}",
                "api_id": api_definition.id,
                "api_name": api_definition.name,
            }
        except Exception as e:
            logger.error(f"Error calling API {api_definition.id}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Error calling API: {str(e)}",
                "api_id": api_definition.id,
                "api_name": api_definition.name,
            }

    async def health_check(self, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if the ERP API is reachable.
        
        Args:
            url: Optional URL to check (defaults to base_url)
        
        Returns:
            Health check result
        """
        check_url = url or self.base_url
        
        try:
            client = await self._get_client()
            response = await client.get(check_url, timeout=5.0)
            
            return {
                "status": "healthy",
                "url": check_url,
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "url": check_url,
                "error": str(e)
            }
