"""
Successful application response model for LoanFlow API.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ApplicationResponse(BaseModel):
    """
    Successful loan application response from API.

    Schema:
        - id (uuid): Unique application identifier
        - applicant_name (string): Applicant full name
        - annual_income (number): Annual income
        - requested_amount (number): Requested loan amount
        - employment_status (string): Employment status
        - status (enum): Application status [pending, approved, rejected, error]
        - risk_score (integer, 0-100, nullable): Risk score from Risk Engine
        - decision_reason (string): Human-readable decision explanation
        - created_at (datetime): Creation timestamp
        - updated_at (datetime): Last update timestamp
    """

    id: str = Field(description="Unique application identifier (UUID)")
    applicant_name: str = Field(description="Applicant full name")
    annual_income: float = Field(ge=0, description="Annual income")
    requested_amount: float = Field(ge=0, description="Requested loan amount")
    employment_status: str = Field(description="Employment status")
    status: str = Field(description="Application status")
    risk_score: Optional[int] = Field(
        default=None, ge=0, le=100, description="Risk score (0-100)"
    )
    decision_reason: Optional[str] = Field(
        default=None, description="Decision explanation"
    )
    created_at: str = Field(description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(description="Last update timestamp (ISO 8601)")

    """Convert API response dictionary to ApplicationResponse object."""

    @classmethod
    def from_dict(cls, data: dict) -> "ApplicationResponse":
        return cls.model_validate(data)
