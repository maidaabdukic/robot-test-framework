"""
Risk Engine scoring logic for LoanFlow mock testing.
"""

from resources.shared.variables.application_status import (
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_REJECTED,
)


class RiskEngineScoringLogic:
    """Scoring algorithm for Risk Engine."""

    @staticmethod
    def calculate_score(annual_income, requested_amount, employment_status):
        """
        Simple scoring logic:
        - Income-to-loan ratio
        - Employment status weighting
        - Return score 0-100
        """
        if annual_income <= 0:
            return 0

        # Lower income-to-loan ratio means the applicant is asking for a
        # larger loan relative to income, which increases risk.
        income_to_loan_ratio = annual_income / requested_amount
        base_score = 100
        ratio_penalty = 0

        # < 0.25 means the requested amount is more than 4x annual income.
        # < 0.5 means the requested amount is more than double annual income.
        # < 1.0 means the requested amount is larger than annual income.
        # < 2.0 means the requested amount is more than half of annual income.
        if income_to_loan_ratio < 0.25:
            ratio_penalty = 75
        elif income_to_loan_ratio < 0.5:
            ratio_penalty = 60
        elif income_to_loan_ratio < 1.0:
            ratio_penalty = 30
        elif income_to_loan_ratio < 2.0:
            ratio_penalty = 15

        base_score -= ratio_penalty

        employment_weights = {
            "employed": 1.0,
            "self_employed": 0.8,
            "retired": 0.9,
            "unemployed": 0.5,
        }
        employment_multiplier = employment_weights.get(employment_status, 0.5)
        score = int(base_score * employment_multiplier)

        return max(0, min(100, score))

    @staticmethod
    def get_decision(score):
        """Translate score to decision."""
        if score >= 70:
            return STATUS_APPROVED
        if 30 <= score < 70:
            return STATUS_PENDING
        return STATUS_REJECTED
