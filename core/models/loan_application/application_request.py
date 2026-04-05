from typing import Optional
from pydantic import BaseModel, Field
from resources.api.variables.business_rules import (
    MIN_LOAN_AMOUNT,
    MAX_LOAN_AMOUNT,
    MIN_APPLICANT_NAME_LENGTH,
    MAX_APPLICANT_NAME_LENGTH,
    MAX_NOTES_LENGTH,
)
from resources.shared.variables.employment_status import EMPLOYMENT_EMPLOYED


class ApplicationRequest(BaseModel):
    """
    Loan application request model.
    Validates against API OpenAPI specification.

    Schema:
        - applicant_name (string): Applicant full name (1-100 characters)
        - annual_income (number): Annual income in currency units (>= 0)
        - requested_amount (number): Loan amount requested (1000.00-500000.00)
        - employment_status (string): Employment status (employed, self_employed, unemployed, retired)
        - notes (string, optional): Free-text notes (max 500 characters)
    """

    applicant_name: str = Field(
        min_length=MIN_APPLICANT_NAME_LENGTH,
        max_length=MAX_APPLICANT_NAME_LENGTH,
        description="Applicant full name",
    )
    annual_income: float = Field(
        ge=0,
        description="Annual income in currency units",
    )
    requested_amount: float = Field(
        ge=MIN_LOAN_AMOUNT,
        le=MAX_LOAN_AMOUNT,
        description="Loan amount requested (1000.00-500000.00)",
    )
    employment_status: str = Field(
        default=EMPLOYMENT_EMPLOYED,
        description="Employment status",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=MAX_NOTES_LENGTH,
        description="Optional free-text notes",
    )
