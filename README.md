# LoanFlow Robot Tests

Automated test framework for the **LoanFlow Application API** built with Robot Framework and Python.

The framework validates the full loan application lifecycle - submission, risk scoring, decision engine, and retrieval - against a self-contained mock environment that starts and stops with each test run. No external services or databases required.

## Goal

Provide a reliable, maintainable, and scalable test suite that:

- Validates business rules (approval thresholds, income ratios, employment-based scoring)
- Runs independently with no external dependencies (mock API + mock risk engine included)
- Is organized for growth - adding new test types (web UI, mobile, performance) requires no restructuring
- Is readable by developers with zero Robot Framework experience

---

## Prerequisites

- Python 3.14+
- pip

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Tests

```bash
source .venv/bin/activate

# Run all API tests
python3 -m robot tests/api/

# Run by tag
python3 -m robot --include smoke tests/api/
python3 -m robot --include negative tests/api/

# Dry-run (syntax and import check, no execution)
python3 -m robot --dryrun tests/api/
```

Local test runs generate `output.xml`, `log.html`, and `report.html` in the project root by default.

In CI, `pull_request` and `push` runs execute linting plus Robot dry-run checks, while the full API suite is currently executed via `workflow_dispatch`.

---

## Project Structure

```
robot-test-framework/
│
├── tests/                                    # Test suites (one folder per test type)
│   └── api/
│       ├── __init__.robot                    # Suite-level settings (shared resource imports)
│       ├── create_application_tests.robot    # 7 tests: lifecycle, rejected, pending, unemployed, risk engine, validation, idempotency
│       └── get_application_tests.robot       # 2 tests: 404 non-existent, retrieve existing application
├── resources/                                # Robot Framework resources (.robot + .py variables)
│   ├── common.robot                          # Shared settings imported by all test suites
│   ├── shared/variables/                     # Constants reused across all test types
│   │   ├── application_status.py             # Application status enum: pending, approved, rejected, error
│   │   └── employment_status.py              # Employment enum: employed, self_employed, etc.
│   └── api/
│       ├── variables/                        # API-specific configuration
│       │   ├── base_urls.py                  # Base URL, mock server URL
│       │   ├── business_rules.py             # Approval thresholds, score ranges, loan limits
│       │   ├── http_status_codes.py          # HTTP status code constants (wraps http.HTTPStatus)
│       │   └── loan_application_defaults.py  # Default test data values
│       └── keywords/
│           └── application_keywords.robot    # High-level composite keywords for assertions
│
├── libraries/                                # Python keyword libraries (registered as RF Library)
│   ├── shared/                               # Generic - usable by any test type
│   │   ├── base_api_client.py                # HTTP transport base class (requests wrapper)
│   │   ├── response_keywords.py              # API response status assertions + error response mapping
│   │   └── mock_server_manager.py            # Start/stop mock servers (suite setup/teardown)
│   └── api/loan_application/                 # Domain-specific - loan application keywords
│       ├── api_keywords.py                   # API calls: submit, get by ID, get all, response mapping
│       ├── data_generator_keywords.py        # Test data scenarios (approved, rejected, edge cases)
│       └── assertion_keywords.py             # Risk score range checks, status assertions
│
├── core/                                     # Pure Python domain layer (no RF dependency)
│   └── models/                               # Pydantic models for request/response validation
│       ├── loan_application/
│       │   ├── application_request.py        # Input model: name, income, amount, employment, notes
│       │   └── application_response.py       # Success response model: id, status, risk_score, timestamps
│       └── error_response.py                 # Error response model: error_code, message, details
│
├── mocks/                                    # Self-contained mock environment
│   ├── application_api_mock.py               # FastAPI app (port 8000) — create/get + decision logic
│   ├── risk_engine_scoring_logic.py          # Scoring algorithm: ratio-based penalty + employment weight
│   ├── mock_request_handler.py               # HTTP handler for risk engine (port 9090)
│   └── wiremock_manager.py                   # Risk Engine lifecycle (custom threaded HTTP server)
│
├── .github/workflows/tests.yml               # CI workflow for linting, dry-run, and API execution
├── robot.toml                                # RobotCode IDE config (python-path = ["."])
├── README.md                                 # Project overview, setup, and architecture notes
├── requirements.txt                          # Python dependencies
└── .gitignore
```

Low-signal files such as `__init__.py` and generated artifacts like `__pycache__/`, `results/`, `log.html`, `report.html`, and `output.xml` are intentionally omitted from the tree above.

### Layer Responsibilities

| Layer        | Purpose                                                                       |
|--------------|-------------------------------------------------------------------------------|
| `tests/`     | Test cases in `.robot` format - what to test                                  |
| `resources/` | Shared keywords (`.robot`) and variables (`.py`) - reusable building blocks   |
| `libraries/` | Python classes whose methods become RF keywords - how to test                 |
| `core/`      | Pydantic models, pure business logic - no framework coupling                  |
| `mocks/`     | FastAPI + HTTP server simulating real services - test infrastructure          |

---

## Test Scenarios

### API Tests - Create Application (`create_application_tests.robot`)

| Test Case | Scenario | Expected Status | Risk Score |
|-----------|----------|-----------------|------------|
| TC-01: Lifecycle + Notification | Submit valid application, verify approval and notification payload | `approved` | 70-100 |
| TC-02: Auto-Rejected (Low Score) | Self-employed, low income-to-loan ratio | `rejected` | 0-29 |
| TC-03: Pending Review | Employed, score ≥ 70 but income-to-loan ratio < 2.0 | `pending` | 70-100 |
| TC-04: Unemployed Over Limit | Unemployed applicant, loan > 10,000 -> auto-rejected | `rejected` | - |
| TC-05: Risk Engine Unavailable | Stop Risk Engine, submit application | `error` | - |
| TC-06: Invalid Amount (400) | Amount below minimum (< 1,000) -> custom `ErrorResponse` built from Pydantic validation | HTTP 400 | - |
| TC-07: Idempotency | Duplicate submission within 60s returns same application | `approved` | 70-100 |

### API Tests — Get Application (`get_application_tests.robot`)

| Test Case | Scenario | Expected HTTP |
|-----------|----------|---------------|
| Get Non-Existent | Request with invalid ID | `404` |
| Get Existing | Create application, retrieve by ID, verify data matches | `200` |

---

## Mock Architecture

Tests run against a fully self-contained mock environment - no real services needed:

```
┌─────────────┐     POST /applications       ┌───────────────────────┐
│  Robot      │ ───────────────────────────► │    Application API    │
│  Framework  │     GET /applications/{id}   │    (FastAPI :8000)    │
│  Tests      │ ◄─────────────────────────── │                       │
└─────────────┘                              │  ┌─────────────────┐  │
                                             │  │ Decision Engine │  │
                                             │  │ (approve,       │  │
                                             │  │ reject, pending)│  │
                                             │  └───────┬─────────┘  │
                                             └──────────┼────────────┘
                                                        │ POST /score
                                                        ▼
                                             ┌───────────────────────┐
                                             │    Risk Engine Mock   │
                                             │     (HTTP :9090)      │
                                             │                       │
                                             │  Score = f(income,    │
                                             │   amount, employment) │
                                             └───────────────────────┘
                                                        │
                                                        │ POST /notify
                                                        ▼
                                             ┌───────────────────────┐
                                             │ Notification Mock Log │
                                             │   (in-process log)    │
                                             └───────────────────────┘
```

**How scoring works:**
1. Application submitted -> API validates input via Pydantic model
2. API calls Risk Engine (`/score`) with income, amount, employment
3. Risk Engine calculates score: base 100, reduced by stepped `income_to_loan_ratio` penalties, then adjusted by employment weighting
4. Application API maps score + `income_to_loan_ratio` to a final status:
   - `approved` when score ≥ 70 and ratio ≥ 2.0
   - `pending` when score is 30-69, or when score ≥ 70 but ratio < 2.0
   - `rejected` when score < 30
5. Additional rule: unemployed applicants with `loan > 10,000` are auto-rejected

**Why mock?** 
Tests must be fast, deterministic, and independent. Real services introduce network latency, data state issues, and flaky failures. Mocks give us full control over every response.

**Mock lifecycle:**
- Test suites start the full mock environment with `Start Mock Servers`
- Each test resets the in-memory application store and notification log with `Reset Mock State`
- Test suites stop it with `Stop Mock Servers`
- The Risk Engine can also be stopped independently inside a test to simulate dependency failure

The local mock environment uses `localhost:8000` for the Application API and `localhost:9090` for the Risk Engine, so test runs may fail if those ports are already in use.

Successful API responses are returned as `ApplicationResponse` objects (or lists of them), while validation and lookup failures return the shared `ErrorResponse` contract.

---

## How to Add New Tests

### New API test scenario

1. Add a data generator method in `libraries/api/feature_name/data_generator_keywords.py`
2. Use it in a `.robot` test file under `tests/api/`

### New API domain (e.g., credit score)

1. Create `libraries/api/credit_score/` with domain-specific keywords
2. Create `tests/api/credit_score_tests.robot`
3. Shared keywords (`response_keywords.py`, `base_api_client.py`) are already available

### New test type (e.g., web UI)

1. Create `libraries/web/pages/` for Page Object Model classes
2. Create `resources/web/keywords/` for composite `.robot` keywords
3. Create `tests/web/` for test suites
4. Structure mirrors `api/` - shared libraries remain in `libraries/shared/`

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| robotframework | 7.0.1 | Test framework |
| requests | 2.31.0 | HTTP client for API calls |
| fastapi | 0.104.1 | Mock Application API |
| uvicorn | 0.24.0 | ASGI server for FastAPI |
| pydantic | (via fastapi) | Request/response model validation |

The Risk Engine mock uses Python's standard-library `http.server`, so no separate mock-server package is required.

## Architecture

The framework follows a **layered, test-type-separated** architecture:

- **`tests/`** - Test suites grouped by type (`api/`, future `web/`, `mobile/`, `performance/`)
- **`resources/shared/`** - Variables reusable across all test types
- **`resources/{type}/`** - Type-specific variables (endpoints, locators) and RF keywords
- **`libraries/shared/`** - Python keyword libraries shared across test types (HTTP status checks, mock servers)
- **`libraries/{type}/`** - Type-specific Python keyword libraries
- **`core/`** - Pure Python (no RF dependency) - Pydantic models, validators
- **`mocks/`** - FastAPI mock API + Python HTTP mock server for risk engine

To add a new test type (e.g., `mobile`), create `tests/mobile/`, `resources/mobile/`, `libraries/mobile/` following the same pattern.

---

## What I Would Add With More Time

- **Parallel execution readiness** - Prepare the framework for safe parallel runs by removing shared mutable state and isolating mock lifecycle management.
- **Deterministic test isolation** - Centralize reset of in-memory state, time-dependent behavior, and generated identifiers so every test remains fully independent and repeatable.
- **Contract-first mock design** - Validate requests and responses against the OpenAPI contract to reduce drift between the mock environment and the real service.
- **Containerized execution model** - Package the mock API and Risk Engine into a reproducible local/CI environment to eliminate machine-specific differences.
- **Observability and diagnostics** - Add structured logging and clearer failure diagnostics for mock-server startup, downstream dependency failures, and asynchronous notification flows.
