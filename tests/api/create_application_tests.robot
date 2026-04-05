*** Settings ***
Documentation    LoanFlow Application API create-application scenarios.
Resource         ../../resources/common.robot
Resource         ../../resources/api/keywords/application_keywords.robot
Variables        ../../resources/api/variables/http_status_codes.py
Library          libraries.api.loan_application.data_generator_keywords.DataGeneratorKeywords
Library          libraries.api.loan_application.api_keywords.ApiKeywords
Library          libraries.shared.response_keywords.ResponseKeywords
Library          libraries.shared.mock_server_manager.MockServerManager
Suite Setup      Start Mock Servers
Suite Teardown   Stop Mock Servers
Test Setup       Reset Mock State


*** Test Cases ***

TC-01: Application Lifecycle - Created and user is Notified
    [Documentation]    Integration test: When a valid application is submitted, 
    ...    Then Risk Engine is called to calculate score and determine status, 
    ...    And application is created with correct values,
    ...    And the Notification Service receives the correct score and status.
    [Tags]    api    regression    smoke    integration
    ${generatedApplication}=    Generate Valid Application Data
    ${response}=    Submit Loan Application    ${generatedApplication}
    Response Status Should Be    ${response}    ${HTTP_201_CREATED}
    ${applicationResponse}=    Create Application Response From Dict    ${response}[body]
    Created Application Response Should Match Request And Business Rules    ${applicationResponse}    ${generatedApplication}    ${STATUS_APPROVED}    ${RISK_SCORE_APPROVED}
    # Wait until the async notification for this application arrives.
    ${notification}=    Wait For Notification    ${response}[body][id]
    Should Be Equal    ${notification}[application_id]    ${response}[body][id]
    Should Be Equal    ${notification}[status]    ${STATUS_APPROVED}

TC-02: Auto-Rejected Based on Risk Score
    [Documentation]    Submit a valid application where expected status is REJECTED based on the low risk score, and verify response object values.
    [Tags]    api    regression    negative    business-rules
    ${generatedApplication}=    Generate Rejected Low Score Application
    ${response}=    Submit Loan Application    ${generatedApplication}
    Response Status Should Be    ${response}    ${HTTP_201_CREATED}
    ${applicationResponse}=    Create Application Response From Dict    ${response}[body]
    Created Application Response Should Match Request And Business Rules    ${applicationResponse}    ${generatedApplication}    ${STATUS_REJECTED}    ${RISK_SCORE_REJECTED}

TC-03: Pending Review Based on Risk Score
    [Documentation]    Submit a valid application with low income/loan ratio, but risk score >= 70, and verify response object values.
    [Tags]    api    regression    business-rules
    ${generatedApplication}=    Generate Pending Application Low Ratio
    ${response}=    Submit Loan Application    ${generatedApplication}
    Response Status Should Be    ${response}    ${HTTP_201_CREATED}
    ${applicationResponse}=    Create Application Response From Dict    ${response}[body]
    Created Application Response Should Match Request And Business Rules    ${applicationResponse}    ${generatedApplication}    ${STATUS_PENDING}    ${RISK_SCORE_PENDING}

TC-04: Unemployed Applicant With High Loan Amount Is Rejected
    [Documentation]    Unemployed applicant requesting > 10,000 is auto-rejected regardless of score.
    [Tags]    api    regression    negative    business-rules
    ${generatedApplication}=    Generate Rejected Unemployed Application
    ${response}=    Submit Loan Application    ${generatedApplication}
    Response Status Should Be    ${response}    ${HTTP_201_CREATED}
    ${applicationResponse}=    Create Application Response From Dict    ${response}[body]
    Should Be Equal    ${applicationResponse.status}    ${STATUS_REJECTED}


TC-05: Error Status When Risk Engine Is Unavailable
    [Documentation]    Stop the Risk Engine, submit an application, and verify it gets status "error".
    [Tags]    api    regression    integration    error-handling
    [Teardown]    Start Risk Engine
    Stop Risk Engine
    ${generatedApplication}=    Generate Application
    ${response}=    Submit Loan Application    ${generatedApplication}
    Response Status Should Be    ${response}    ${HTTP_201_CREATED}
    ${applicationResponse}=    Create Application Response From Dict    ${response}[body]
    Should Be Equal    ${applicationResponse.status}    ${STATUS_ERROR}
    Should Be Equal    ${applicationResponse.risk_score}    ${None}

TC-06: Invalid Application With Low Amount Returns 400
    [Documentation]    Submit an application with an amount below the minimum and verify
    ...                the API returns 400 Bad Request with the custom ErrorResponse payload.
    [Tags]    api    regression    negative    validation
    ${invalidApplication}=    Generate Invalid Application With Amount Below Minimum
    ${response}=    Submit Loan Application    ${invalidApplication}
    Response Status Should Be    ${response}    ${HTTP_400_BAD_REQUEST}
    ${error}=    Create Error Response From Dict    ${response}[body]
    Should Be Equal    ${error.error_code}    VALIDATION_ERROR
    Should Not Be Empty    ${error.details}
    Should Be Equal    ${error.message}    ${error.details}[0]
    Should Contain    ${error.message}    requested_amount
    Should Contain    ${error.details}[0]    requested_amount

TC-07: Duplicate Application Within Idempotency Window Returns First Sent Application
    [Documentation]    Submitting the same name+amount within 60s returns the existing application.
    [Tags]    api    idempotency
    ${generatedApplication}=    Generate Valid Application Data
    ${first_response}=    Submit Loan Application    ${generatedApplication}
    Response Status Should Be    ${first_response}    ${HTTP_201_CREATED}
    ${second_response}=    Submit Loan Application    ${generatedApplication}
    Response Status Should Be    ${second_response}    ${HTTP_201_CREATED}
    Should Be Equal    ${first_response}[body][id]    ${second_response}[body][id]
    Should Be Equal    ${first_response}[body]    ${second_response}[body]
