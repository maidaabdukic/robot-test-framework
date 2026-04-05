"""
Base API client for Robot Framework keyword libraries.
Shared HTTP transport — inherit to add domain-specific endpoints.
"""

import requests
from typing import Dict, Any

from resources.api.variables.base_urls import API_BASE_URL
from resources.api.variables.business_rules import API_TIMEOUT_SECONDS


class BaseApiClient:
    """Reusable HTTP transport for API keyword libraries."""

    def __init__(
        self, base_url: str = API_BASE_URL, timeout: int = API_TIMEOUT_SECONDS
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.last_response = None

    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Execute HTTP request and return standardised response dict."""
        try:
            response = self.session.request(
                method,
                f"{self.base_url}{path}",
                timeout=self.timeout,
                **kwargs,
            )
            return {
                "status": response.status_code,
                "body": response.json() if response.text else None,
            }
        except Exception as e:
            return {"status": 0, "error": str(e)}
