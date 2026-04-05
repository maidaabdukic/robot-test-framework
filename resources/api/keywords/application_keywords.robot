*** Settings ***
Documentation    Reusable keywords for loan application assertions.
Resource         ../../common.robot
Library          libraries.api.loan_application.assertion_keywords.AssertionKeywords

*** Keywords ***

Created Application Response Should Match Request And Business Rules
    [Documentation]    Verify application response fields match the request and expected outcome.
    [Arguments]    ${applicationResponse}    ${createdApplicationObject}    ${expected_status}    ${expected_score_range}
    Should Not Be Empty    ${applicationResponse.id}
    Should Be Equal    ${applicationResponse.applicant_name}    ${createdApplicationObject.applicant_name}
    Should Be Equal As Numbers    ${applicationResponse.annual_income}    ${createdApplicationObject.annual_income}
    Should Be Equal As Numbers    ${applicationResponse.requested_amount}    ${createdApplicationObject.requested_amount}
    Should Be Equal    ${applicationResponse.employment_status}    ${createdApplicationObject.employment_status}
    Should Be Equal    ${applicationResponse.status}    ${expected_status}
    Should Not Be Equal    ${applicationResponse.risk_score}    ${None}
    Risk Score Should Be In Range    ${applicationResponse.risk_score}    ${expected_score_range}
