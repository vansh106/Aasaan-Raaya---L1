"""
ERP Service - Handles communication with the ERP system.

This service makes HTTP calls to the ERP API to fetch data like:
- Bootstrap data (company, projects, suppliers, modules)
- Other ERP-specific endpoints as needed
"""

import httpx
from typing import Dict, Any, Optional
from config import settings
import logging

logger = logging.getLogger(__name__)


class ERPService:
    """Service for communicating with the ERP system"""

    def __init__(self):
        self.base_url = settings.erp_base_url
        self.timeout = settings.erp_api_timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client with connection pooling"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            )
        return self._client

    async def close(self):
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def fetch_bootstrap(self, company_id: str) -> Dict[str, Any]:
        """
        Fetch bootstrap data from ERP for a company.
        
        This calls: GET {ERP_BASE_URL}/bootstrap?company_id={company_id}
        
        Returns:
            {
                "success": true,
                "data": {
                    "company": {...},
                    "projects": [...],
                    "suppliers": [...],
                    "modules": [...]
                }
            }
        """
        try:
            client = await self._get_client()
            
            url = f"{self.base_url}/bootstrap"
            params = {"company_id": company_id}
            
            logger.info(f"Fetching bootstrap data from {url} for company {company_id}")
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(
                f"Bootstrap data fetched successfully: "
                f"{len(data.get('data', {}).get('projects', []))} projects, "
                f"{len(data.get('data', {}).get('suppliers', []))} suppliers"
            )
            
            return data

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching bootstrap data for company {company_id}")
            return {
                "success": False,
                "error": f"Request timeout after {self.timeout} seconds"
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching bootstrap: {e.response.status_code}")
            return {
                "success": False,
                "error": f"HTTP error {e.response.status_code}: {str(e)}"
            }
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching bootstrap: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error fetching bootstrap: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Error fetching bootstrap: {str(e)}"
            }

    async def call_api(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a generic API call to the ERP system.
        
        Args:
            endpoint: API endpoint path (e.g., "/supplierpayables-get")
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Request body data
            headers: Additional headers
            
        Returns:
            API response or error dict
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}{endpoint}"
            
            logger.debug(f"Calling ERP API: {method} {url}")
            
            if method.upper() == "GET":
                response = await client.get(url, params=params, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(
                    url, params=params, json=data, headers=headers
                )
            elif method.upper() == "PUT":
                response = await client.put(
                    url, params=params, json=data, headers=headers
                )
            elif method.upper() == "DELETE":
                response = await client.delete(url, params=params, headers=headers)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            response.raise_for_status()
            
            try:
                result = response.json()
            except Exception:
                result = response.text
            
            return {
                "success": True,
                "status_code": response.status_code,
                "data": result
            }

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling ERP API: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error calling ERP API: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Error: {str(e)}"
            }


# Global ERP service instance
erp_service = ERPService()

