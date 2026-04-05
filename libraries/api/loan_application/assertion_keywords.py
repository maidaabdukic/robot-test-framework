"""
Robot Framework keyword library — response assertions.
Risk score range checks.
"""


class AssertionKeywords:
    """Assertion keywords for LoanFlow tests."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    # --- Application fields ---

    def application_should_have_risk_score(self, response):
        body = response.get("body", {})
        assert "risk_score" in body and body.get("risk_score") is not None, (
            "Application response is missing risk score."
        )

    def application_status_should_be(self, response, status):
        body = response.get("body", {})
        assert body.get("status") == status, (
            f"Expected status '{status}', got '{body.get('status')}'."
        )

    # --- Risk score range ---

    @staticmethod
    def _score_matches_range(score, score_range):
        min_score, max_score, max_inclusive = (
            float(score_range[0]),
            float(score_range[1]),
            bool(score_range[2]),
        )
        if max_inclusive:
            return min_score <= score <= max_score
        return min_score <= score < max_score

    def risk_score_should_be_in_range(self, score, score_range):
        """Assert score matches one or more expected range tuples."""
        score = float(score)
        ranges = (
            score_range if isinstance(score_range[0], (list, tuple)) else (score_range,)
        )
        assert any(
            self._score_matches_range(score, expected_range)
            for expected_range in ranges
        ), f"Risk score {score} not in allowed ranges {ranges}"

    def risk_score_should_be_valid(self, response):
        """Assert risk score is None or a number between 0 and 100."""
        body = response.get("body", {})
        score = body.get("risk_score")
        assert score is None or (
            isinstance(score, (int, float)) and 0 <= score <= 100
        ), f"Risk score {score} is not valid (should be 0-100 or None)."
