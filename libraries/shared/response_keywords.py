"""
Robot Framework keyword library — response assertions.
"""

from core.models import ErrorResponse


class ResponseKeywords:
    """Assertion keywords for API response statuses."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    # Error response mapping

    def create_error_response_from_dict(self, response_dict: dict) -> ErrorResponse:
        return ErrorResponse.from_dict(response_dict)

    # HTTP status assertions

    def response_status_should_be(self, response, expected_status):
        actual = response.get("status")
        assert actual == int(expected_status), (
            f"Expected status {expected_status}, got {actual}"
        )

    def response_should_indicate_success(self, response):
        assert 200 <= response.get("status", 0) < 300, (
            f"Expected success (2xx), got {response.get('status')}"
        )

    def response_is_validation_error(self, response):
        assert response.get("status") == 400, (
            f"Expected 400, got {response.get('status')}"
        )

    def response_is_not_found(self, response):
        assert response.get("status") == 404, (
            f"Expected 404, got {response.get('status')}"
        )

    def response_is_service_unavailable(self, response):
        assert response.get("status") == 503, (
            f"Expected 503, got {response.get('status')}"
        )

    # Model class/object validation

    def response_should_match_object(self, response, model_class):
        """Validate response body against a Pydantic model class/object."""
        body = response.get("body", {})
        model_class.model_validate(body)
