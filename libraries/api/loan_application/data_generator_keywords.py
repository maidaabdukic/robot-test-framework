"""
Robot Framework keyword library — test data generation.
All scenarios defined directly; no external generator dependency.
"""

from typing import Dict, Any
from core.models.loan_application.application_request import ApplicationRequest
from resources.api.variables.loan_application_defaults import (
    DEFAULT_AMOUNT,
    DEFAULT_EMPLOYMENT,
    DEFAULT_INCOME,
    DEFAULT_NAME,
    DEFAULT_NOTES,
)
from resources.shared.variables.employment_status import (
    EMPLOYMENT_EMPLOYED,
    EMPLOYMENT_SELF_EMPLOYED,
    EMPLOYMENT_UNEMPLOYED,
    EMPLOYMENT_RETIRED,
)


class DataGeneratorKeywords:
    """Data generation keywords for LoanFlow tests."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    # -------------------------------------------------------------------------
    # Base generator
    # -------------------------------------------------------------------------

    @staticmethod
    def generate_application(
        name: str = DEFAULT_NAME,
        annual_income: float = DEFAULT_INCOME,
        requested_amount: float = DEFAULT_AMOUNT,
        employment_status: str = DEFAULT_EMPLOYMENT,
        notes: str = DEFAULT_NOTES,
    ) -> ApplicationRequest:
        """Generate a loan application with default values, or override with provided values."""
        return ApplicationRequest(
            applicant_name=name,
            annual_income=annual_income,
            requested_amount=requested_amount,
            employment_status=employment_status,
            notes=notes,
        )

    # -------------------------------------------------------------------------
    # APPROVED scenarios  (score >= 70 AND income/loan >= 2.0)
    # -------------------------------------------------------------------------

    def generate_valid_application_data(self):
        """Employed applicant: score=100, ratio=2.8 -> APPROVED."""
        return self.generate_application(
            name="Employed Approved",
            annual_income=70000.00,
            requested_amount=25000.00,
            employment_status=EMPLOYMENT_EMPLOYED,
        )

    def generate_approved_application(self):
        """Employed applicant: score=100, ratio=2.8 -> APPROVED."""
        return self.generate_application(
            name="Employed Approved",
            annual_income=70000.00,
            requested_amount=25000.00,
            employment_status=EMPLOYMENT_EMPLOYED,
        )

    def generate_approved_self_employed_application(self):
        """Self-employed applicant: score=80, ratio=2.5 -> APPROVED."""
        return self.generate_application(
            name="Self-Employed Approved",
            annual_income=100000.00,
            requested_amount=40000.00,
            employment_status=EMPLOYMENT_SELF_EMPLOYED,
        )

    def generate_approved_retired_application(self):
        """Retired applicant: score=90, ratio=3.0 -> APPROVED."""
        return self.generate_application(
            name="Retired Approved",
            annual_income=60000.00,
            requested_amount=20000.00,
            employment_status=EMPLOYMENT_RETIRED,
        )

    # -------------------------------------------------------------------------
    # PENDING scenarios  (score 30-69 OR score >= 70 but income/loan < 2.0)
    # -------------------------------------------------------------------------

    def generate_pending_application_low_ratio(self):
        """Employed, score=85 but income/loan=1.5 < 2.0 -> PENDING."""
        return self.generate_application(
            name="Employed LowRatio Pending",
            annual_income=30000.00,
            requested_amount=20000.00,
            employment_status=EMPLOYMENT_EMPLOYED,
        )

    def generate_pending_application_low_score(self):
        """Self-employed, score=68 and income/loan=1.2 < 2.0 -> PENDING."""
        return self.generate_application(
            name="Self-Employed Pending",
            annual_income=60000.00,
            requested_amount=50000.00,
            employment_status=EMPLOYMENT_SELF_EMPLOYED,
        )

    # -------------------------------------------------------------------------
    # REJECTED scenarios  (score < 30 OR unemployed AND amount > 10,000)
    # -------------------------------------------------------------------------

    def generate_rejected_unemployed_application(self):
        """Unemployed, score=50, amount > 10,000 -> auto-REJECTED by business rule."""
        return self.generate_application(
            name="Unemployed Over Limit",
            annual_income=40000.00,
            requested_amount=10001.00,
            employment_status=EMPLOYMENT_UNEMPLOYED,
        )

    def generate_rejected_low_score_application(self):
        """Self-employed, score=20 and income/loan=0.05 -> REJECTED on low score."""
        return self.generate_application(
            name="Self-Employed Low Score",
            annual_income=3600.00,
            requested_amount=70000.00,
            employment_status=EMPLOYMENT_SELF_EMPLOYED,
        )

    # -------------------------------------------------------------------------
    # Edge cases
    # -------------------------------------------------------------------------

    def generate_edge_exact_approval_ratio(self):
        """Exact boundary: income/amount = 2.0, score=100 -> APPROVED."""
        return self.generate_application(
            name="Employed Exact Ratio",
            annual_income=50000.00,
            requested_amount=25000.00,
            employment_status=EMPLOYMENT_EMPLOYED,
        )

    def generate_edge_just_below_approval_ratio(self):
        """income/loan = 1.99 (just below 2.0), score=85 -> PENDING."""
        return self.generate_application(
            name="Employed Just Below Ratio",
            annual_income=50000.00,
            requested_amount=25100.00,
            employment_status=EMPLOYMENT_EMPLOYED,
        )

    def generate_edge_unemployed_at_limit(self):
        """Unemployed, score=50, amount = 10,000 (not > 10,000) -> PENDING."""
        return self.generate_application(
            name="Unemployed At Limit",
            annual_income=30000.00,
            requested_amount=10000.00,
            employment_status=EMPLOYMENT_UNEMPLOYED,
        )

    def generate_edge_unemployed_over_limit(self):
        """Unemployed, score=50, amount = 10,001 -> auto-REJECTED by business rule."""
        return self.generate_application(
            name="Unemployed Over Limit",
            annual_income=30000.00,
            requested_amount=10001.00,
            employment_status=EMPLOYMENT_UNEMPLOYED,
        )

    # -------------------------------------------------------------------------
    # Invalid / validation-error scenarios - return raw dict to bypass Pydantic
    # -------------------------------------------------------------------------

    def generate_invalid_application_with_missing_field(
        self, field_to_omit: str
    ) -> Dict[str, Any]:
        """Missing required field -> Bad Request (400)."""
        data = self.generate_application().model_dump(exclude_none=True)
        del data[field_to_omit]
        return data

    def generate_invalid_application_with_amount_below_minimum(self) -> Dict[str, Any]:
        """Amount below 1,000 minimum -> Bad Request (400)."""
        data = self.generate_application().model_dump(exclude_none=True)
        data["requested_amount"] = 999.00
        return data

    def generate_invalid_application_with_amount_above_maximum(self) -> Dict[str, Any]:
        """Amount above 500,000 maximum -> Bad Request (400)."""
        data = self.generate_application().model_dump(exclude_none=True)
        data["requested_amount"] = 500001.00
        return data

    def generate_invalid_application_with_long_name(self) -> Dict[str, Any]:
        """Name exceeding 100 character maximum -> Bad Request (400)."""
        data = self.generate_application().model_dump(exclude_none=True)
        data["applicant_name"] = "A" * 101
        return data
