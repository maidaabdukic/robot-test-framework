"""
Mock Application API for LoanFlow testing.
Provides a FastAPI-based implementation of the REST API.
Calls the Risk Engine mock for scoring.
"""

import os
import sys
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import ValidationError, BaseModel
from pydantic_core import ErrorDetails
from datetime import datetime
import uuid
import asyncio
import requests

from resources.api.variables.base_urls import MOCK_SERVER_URL
from resources.api.variables.business_rules import (
    API_TIMEOUT_SECONDS,
    APPROVAL_RISK_SCORE,
    REJECTION_RISK_SCORE,
    MIN_INCOME_TO_LOAN_RATIO,
    UNEMPLOYED_MAX_LOAN,
    IDEMPOTENCY_WINDOW_SECONDS,
)

# Ensure project root is on path for package imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from resources.shared.variables.application_status import (
    STATUS_PENDING,
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_ERROR,
    VALID_APPLICATION_STATUSES,
)
from resources.shared.variables.employment_status import EMPLOYMENT_UNEMPLOYED
from core.models.error_response import ErrorResponse
from core.models.loan_application.application_request import ApplicationRequest
from core.models.loan_application.application_response import ApplicationResponse

app = FastAPI(title="LoanFlow Application API", version="1.0.0")


class RawRequest(BaseModel):
    """Accept raw JSON without validation — validate manually to return 400."""

    class Config:
        extra = "allow"  # Accept any extra fields
        json_schema_extra = {"example": {}}


# In-memory storage for applications (for testing only)
applications_db = {}
# Index for idempotency checks: (applicant_name, requested_amount) -> app_id
_idempotency_index = {}


def build_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: list[str] | None = None,
):
    """Return a consistent API error payload."""
    error = ErrorResponse(
        error_code=error_code,
        message=message,
        details=details,
    )
    return JSONResponse(
        status_code=status_code,
        content=error.model_dump(exclude_none=True),
    )


def format_validation_errors(errors: list[ErrorDetails]) -> list[str]:
    """Convert Pydantic validation errors to user-facing strings."""
    formatted_errors = []
    for error in errors:
        location = ".".join(str(part) for part in error.get("loc", []))
        message = error.get("msg", "Invalid value.")
        formatted_errors.append(f"{location}: {message}" if location else message)
    return formatted_errors


# ============================================================================
# Risk Engine Integration
# ============================================================================


async def call_risk_engine(annual_income, requested_amount, employment_status):
    """
    Call the Risk Engine mock service to get score and decision.
    """
    payload = {
        "annual_income": annual_income,
        "requested_amount": requested_amount,
        "employment_status": employment_status,
    }

    def _post_score():
        return requests.post(
            f"{MOCK_SERVER_URL}/score",
            json=payload,
            timeout=API_TIMEOUT_SECONDS,
        )

    try:
        response = await asyncio.to_thread(_post_score)
        if response.status_code == 200:
            data = response.json()
            return data.get("score"), data.get("decision")
        return None, None
    except requests.exceptions.Timeout:
        return None, None
    except Exception:
        return None, None


async def notify_application(application: dict):
    """
    Fire-and-forget notification to Notification Service.
    """
    payload = {
        "application_id": application["id"],
        "applicant_name": application["applicant_name"],
        "status": application["status"],
        "decision_reason": application["decision_reason"],
    }

    def _post_notify():
        return requests.post(
            f"{MOCK_SERVER_URL}/notify",
            json=payload,
            timeout=API_TIMEOUT_SECONDS,
        )

    try:
        await asyncio.to_thread(_post_notify)
    except Exception:
        pass


# ============================================================================
# Endpoints
# ============================================================================


@app.post(
    "/api/v1/applications",
    status_code=201,
    response_model=ApplicationResponse,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Validation error response.",
        }
    },
)
async def create_application(raw_request: RawRequest):
    """Create a new loan application.
    Internally calls the Risk Engine mock to get a score and determine approval status.
    POST /applications"""

    # Convert to dict and validate using Pydantic — returns 400 if invalid
    request_dict = raw_request.model_dump()
    try:
        request_data = ApplicationRequest.model_validate(request_dict)
    except ValidationError as e:
        validation_messages = format_validation_errors(e.errors())
        return build_error_response(
            status_code=400,
            error_code="VALIDATION_ERROR",
            message=validation_messages[0]
            if validation_messages
            else "Request validation failed.",
            details=validation_messages,
        )
    idempotency_key = (request_data.applicant_name, request_data.requested_amount)
    if idempotency_key in _idempotency_index:
        existing_id = _idempotency_index[idempotency_key]
        existing = applications_db.get(existing_id)
        if existing:
            created_at = datetime.fromisoformat(existing["created_at"].rstrip("Z"))
            if (
                datetime.now() - created_at
            ).total_seconds() < IDEMPOTENCY_WINDOW_SECONDS:
                return existing

    # Generate application ID
    app_id = str(uuid.uuid4())
    now = datetime.now().isoformat() + "Z"

    # Call Risk Engine to get score and decision
    score, risk_engine_decision = await call_risk_engine(
        request_data.annual_income,
        request_data.requested_amount,
        request_data.employment_status,
    )

    # Determine status and decision reason based on business rules
    if score is None:
        status = STATUS_ERROR
        decision_reason = "Risk Engine unavailable."
        risk_score = None
    else:
        risk_score = score
        risk_engine_decision = risk_engine_decision or (
            STATUS_APPROVED
            if score >= APPROVAL_RISK_SCORE
            else STATUS_REJECTED
            if score < REJECTION_RISK_SCORE
            else STATUS_PENDING
        )
        income_to_loan_ratio = (
            request_data.annual_income / request_data.requested_amount
        )
        is_unemployed = request_data.employment_status == EMPLOYMENT_UNEMPLOYED

        if is_unemployed and request_data.requested_amount > UNEMPLOYED_MAX_LOAN:
            status = STATUS_REJECTED
            decision_reason = "Application declined due to high risk."
        elif (
            risk_engine_decision == STATUS_APPROVED
            and income_to_loan_ratio >= MIN_INCOME_TO_LOAN_RATIO
        ):
            status = STATUS_APPROVED
            decision_reason = "Eligible for approval based on risk assessment."
        elif risk_engine_decision == STATUS_REJECTED:
            status = STATUS_REJECTED
            decision_reason = "Application declined due to high risk."
        else:
            status = STATUS_PENDING
            decision_reason = "Application requires manual review."

    # Create application object
    application = ApplicationResponse(
        id=app_id,
        applicant_name=request_data.applicant_name,
        annual_income=request_data.annual_income,
        requested_amount=request_data.requested_amount,
        employment_status=request_data.employment_status,
        status=status,
        risk_score=risk_score,
        decision_reason=decision_reason,
        created_at=now,
        updated_at=now,
    )

    # Store in memory and update idempotency index
    applications_db[app_id] = application.model_dump()
    _idempotency_index[idempotency_key] = app_id

    # Notify asynchronously (fire-and-forget)
    asyncio.create_task(notify_application(applications_db[app_id]))

    return application


@app.get(
    "/api/v1/applications",
    response_model=list[ApplicationResponse],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Invalid status filter.",
        }
    },
)
async def list_applications(status: str | None = None):
    """List all applications.\n
    GET /applications
    """
    apps = list(applications_db.values())

    if status:
        valid_statuses = VALID_APPLICATION_STATUSES
        if status not in valid_statuses:
            return build_error_response(
                status_code=400,
                error_code="INVALID_PARAMETER",
                message=f"status must be one of: {', '.join(valid_statuses)}",
            )
        apps = [app for app in apps if app["status"] == status]

    return apps


@app.get(
    "/api/v1/applications/{id}",
    response_model=ApplicationResponse,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Application not found.",
        }
    },
)
async def get_application(id: str):
    """Get application by ID.\n
    GET /applications/{id}"""
    if id not in applications_db:
        return build_error_response(
            status_code=404,
            error_code="NOT_FOUND",
            message=f"Application {id} not found",
        )

    return applications_db[id]


@app.get("/health")
async def health():
    """Health check endpoint for mock servers."""
    return {"status": "healthy"}


def reset_database():
    """Clear all applications - useful for test setup/teardown."""
    global applications_db, _idempotency_index
    applications_db = {}
    _idempotency_index = {}
