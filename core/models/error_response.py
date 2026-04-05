"""
Error response model for LoanFlow API.
"""

from typing import List, Optional

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """
    API error response.

    Schema:
        - error_code (string): Machine-readable error code (e.g., INVALID_PARAMETER, NOT_FOUND)
        - message (string): Human-readable error message
        - details (list of strings, optional): Additional validation or debugging messages
    """

    error_code: str
    message: str
    details: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ErrorResponse":
        """Convert API response dictionary to ErrorResponse object."""
        return cls.model_validate(data)
