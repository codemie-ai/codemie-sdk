"""Unit tests for the requests ServiceNowIntegrationService sends and the responses it parses."""

import json
from unittest.mock import MagicMock, patch

import pytest

from codemie_sdk.models.servicenow_integration import (
    ServiceNowBudgetAction,
    ServiceNowBudgetRequest,
)
from codemie_sdk.services.servicenow_integration import ServiceNowIntegrationService

_BUDGET_RESPONSE = {
    "project_name": "demo-project",
    "cost_center": "abc-def",
    "created_project": True,
    "created_cost_center": True,
    "budget": {
        "total_amount": 150.0,
        "budget_duration": "30d",
        "categories": [
            {
                "category": "platform",
                "max_budget": 100.0,
                "soft_budget": 80.0,
                "budget_reset_at": None,
            },
            {
                "category": "cli",
                "max_budget": 50.0,
                "soft_budget": 40.0,
                "budget_reset_at": None,
            },
        ],
    },
    "admins_assigned": ["a@example.com"],
    "admins_pending": ["b@example.com"],
}


@pytest.fixture
def service():
    return ServiceNowIntegrationService("https://api.example.com", "token")


def _response(payload):
    response = MagicMock()
    response.status_code = 200
    response.content = json.dumps(payload).encode()
    response.json.return_value = payload
    return response


def test_list_projects_sends_each_email_and_parses_items(service):
    payload = [
        {"project_name": "alpha", "display_name": "Alpha"},
        {"project_name": "beta", "display_name": None},
    ]
    with patch(
        "codemie_sdk.utils.http.requests.get", return_value=_response(payload)
    ) as get:
        projects = service.list_projects(["a@example.com", "b@example.com"])

    assert get.call_args.kwargs["url"].endswith("/v1/integrations/servicenow/projects")
    assert get.call_args.kwargs["params"] == {
        "emails": ["a@example.com", "b@example.com"]
    }
    assert [(p.project_name, p.display_name) for p in projects] == [
        ("alpha", "Alpha"),
        ("beta", None),
    ]


def test_list_projects_returns_empty_list_when_nothing_matches(service):
    with patch("codemie_sdk.utils.http.requests.get", return_value=_response([])):
        assert service.list_projects(["nobody@example.com"]) == []


def test_submit_budget_request_sends_body_and_parses_response(service):
    request = ServiceNowBudgetRequest(
        action=ServiceNowBudgetAction.SET,
        request_id="RQ-1",
        epam_project_code="abc-def",
        admin_emails=["a@example.com"],
        amounts={"platform": 100.0, "cli": 50.0},
    )
    with patch(
        "codemie_sdk.utils.http.requests.post",
        return_value=_response(_BUDGET_RESPONSE),
    ) as post:
        result = service.submit_budget_request(request)

    assert post.call_args.kwargs["url"].endswith("/v1/integrations/servicenow/budgets")
    assert json.loads(post.call_args.kwargs["data"]) == {
        "action": "set",
        "request_id": "RQ-1",
        "epam_project_code": "abc-def",
        "admin_emails": ["a@example.com"],
        "amounts": {"platform": 100.0, "cli": 50.0},
    }
    assert result.created_project is True
    assert result.cost_center == "abc-def"
    assert [c.category for c in result.budget.categories] == ["platform", "cli"]
    assert result.budget.total_amount == 150.0
    assert result.admins_pending == ["b@example.com"]


def test_submit_budget_request_parses_null_budget_after_cancel(service):
    payload = {**_BUDGET_RESPONSE, "budget": None}
    request = ServiceNowBudgetRequest(
        action=ServiceNowBudgetAction.CANCEL,
        request_id="RQ-2",
        epam_project_code="abc-def",
    )
    with patch(
        "codemie_sdk.utils.http.requests.post", return_value=_response(payload)
    ) as post:
        result = service.submit_budget_request(request)

    sent = json.loads(post.call_args.kwargs["data"])
    assert "amounts" not in sent and "codemie_project_name" not in sent
    assert result.budget is None


def test_submit_budget_request_sends_non_finite_amount_as_json_constant(service):
    request = ServiceNowBudgetRequest(
        action=ServiceNowBudgetAction.SET,
        request_id="RQ-3",
        epam_project_code="abc-def",
        amounts={"platform": float("nan")},
    )
    with patch(
        "codemie_sdk.utils.http.requests.post",
        return_value=_response(_BUDGET_RESPONSE),
    ) as post:
        service.submit_budget_request(request)

    assert '"platform":NaN' in post.call_args.kwargs["data"].replace(" ", "")
