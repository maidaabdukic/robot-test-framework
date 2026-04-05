"""
Robot Framework keyword library — API interactions.
Loan application endpoints.
"""

from typing import List, Optional
from libraries.shared.base_api_client import BaseApiClient
from core.models import ApplicationResponse


class ApiKeywords(BaseApiClient):
    """API interaction keywords for LoanFlow loan applications."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    # --- Loan application endpoints ---

    def submit_loan_application(self, application_data):
        if hasattr(application_data, "model_dump"):
            application_data = application_data.model_dump(exclude_none=True)
        response = self._request("POST", "/applications", json=application_data)
        self.last_response = response
        return response

    def get_application_by_id(self, app_id):
        response = self._request("GET", f"/applications/{app_id}")
        self.last_response = response
        return response

    def get_all_applications(self, status: Optional[str] = None):
        params = {"status": status} if status else {}
        response = self._request("GET", "/applications", params=params)
        self.last_response = response
        return response

    # --- Utility ---

    def get_application_id_from_response(self, response):
        return response.get("body", {}).get("id")

    # --- Response mapping ---

    def create_application_response_from_dict(
        self, response_dict: dict
    ) -> ApplicationResponse:
        return ApplicationResponse.from_dict(response_dict)

    def create_application_list_from_dict(
        self, response_list: list
    ) -> List[ApplicationResponse]:
        return [ApplicationResponse.from_dict(item) for item in response_list]
