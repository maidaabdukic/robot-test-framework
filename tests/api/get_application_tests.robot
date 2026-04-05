*** Settings ***
Documentation    API tests for retrieving loan applications.
Resource         ../../resources/common.robot
Variables        ../../resources/api/variables/http_status_codes.py
Library          libraries.api.loan_application.api_keywords.ApiKeywords
Library          libraries.shared.response_keywords.ResponseKeywords
Library          libraries.api.loan_application.data_generator_keywords.DataGeneratorKeywords
Library          libraries.shared.mock_server_manager.MockServerManager
Suite Setup      Start Mock Servers
Suite Teardown   Stop Mock Servers
Test Setup       Reset Mock State

*** Test Cases ***

TC-08: Get Non-Existent Application Returns 404
    [Documentation]    Verify that requesting a non-existent application returns 404.
    [Tags]    negative    api
    ${response}=    Get Application By Id    non-existent-id-12345
    Response Status Should Be    ${response}    ${HTTP_404_NOT_FOUND}
    ${error}=    Create Error Response From Dict    ${response}[body]
    Should Be Equal    ${error.error_code}    NOT_FOUND
    Should Contain    ${error.message}    non-existent-id-12345
    Should Be Equal    ${error.details}    ${None}

TC-09: Get Existing Application Returns Correct Data
    [Documentation]    Create an application, then retrieve it and verify the data matches.
    [Tags]    api   regression
    ${generatedApplication}=    Generate Valid Application Data
    ${created_application}=    Submit Loan Application    ${generatedApplication}
    Response Status Should Be    ${created_application}    ${HTTP_201_CREATED}
    ${get_response}=    Get Application By Id    ${created_application}[body][id]
    Response Status Should Be    ${get_response}    ${HTTP_200_OK}
    ${created_object}=    Create Application Response From Dict    ${created_application}[body]
    ${retrieved_object}=    Create Application Response From Dict    ${get_response}[body]
    Should Be Equal    ${created_object}    ${retrieved_object}
