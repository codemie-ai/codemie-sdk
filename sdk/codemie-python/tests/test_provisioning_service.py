# Copyright 2026 EPAM Systems, Inc. ("EPAM")
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for the requests ProvisioningService sends and the responses it parses."""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from codemie_sdk.models.provisioning import (
    ProvisioningBudgetRequest,
    ProvisioningProjectBlock,
)
from codemie_sdk.services.provisioning import ProvisioningService

_BASE = "https://api.example.com/v1/provisioning/projects"
_BUDGET_RESPONSE = {
    "project_name": "demo-project",
    "cost_center": "abc-def",
    "created_project": True,
    "created_cost_center": True,
    "created_budget": True,
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
                "budget_reset_at": "2026-11-18T00:00:00Z",
            },
        ],
    },
    "admins_assigned": ["a@example.com"],
    "admins_not_assigned": ["b@example.com"],
}


@pytest.fixture
def service() -> ProvisioningService:
    return ProvisioningService("https://api.example.com", "token")


def _response(status_code: int, payload=None) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.content = b"" if payload is None else json.dumps(payload).encode()
    response.json.return_value = payload
    return response


def test_list_projects_sends_each_email_and_parses_items(service):
    payload = [
        {"project_name": "alpha", "display_name": "Alpha"},
        {"project_name": "beta", "display_name": None},
    ]
    with patch(
        "codemie_sdk.utils.http.requests.get", return_value=_response(200, payload)
    ) as get:
        projects = service.list_projects(["a@example.com", "b@example.com"])

    assert get.call_args.kwargs["url"] == _BASE
    assert get.call_args.kwargs["params"] == {
        "member_email": ["a@example.com", "b@example.com"]
    }
    assert [(p.project_name, p.display_name) for p in projects] == [
        ("alpha", "Alpha"),
        ("beta", None),
    ]


def test_set_budget_sends_put_with_reference_and_returns_status_and_body(service):
    request = ProvisioningBudgetRequest(
        amounts={"platform": 100.0, "cli": 50.0},
        project=ProvisioningProjectBlock(
            cost_center="abc-def", admin_emails=["a@example.com"]
        ),
    )
    with patch(
        "codemie_sdk.services.provisioning.requests.request",
        return_value=_response(201, _BUDGET_RESPONSE),
    ) as send:
        result = service.set_budget("demo-project", "CHG-1", request)

    assert send.call_args.args == ("PUT", f"{_BASE}/demo-project/budget")
    assert send.call_args.kwargs["headers"]["X-Change-Reference"] == "CHG-1"
    assert send.call_args.kwargs["headers"]["Authorization"] == "Bearer token"
    assert json.loads(send.call_args.kwargs["data"]) == {
        "amounts": {"platform": 100.0, "cli": 50.0},
        "project": {"cost_center": "abc-def", "admin_emails": ["a@example.com"]},
    }
    assert result.status_code == 201
    assert result.budget.created_budget is True
    assert [c.category for c in result.budget.budget.categories] == ["platform", "cli"]
    assert result.budget.admins_not_assigned == ["b@example.com"]


def test_adjust_budget_sends_patch_and_keeps_an_empty_project_block(service):
    request = ProvisioningBudgetRequest(
        amounts={"cli": 0.0}, project=ProvisioningProjectBlock()
    )
    with patch(
        "codemie_sdk.services.provisioning.requests.request",
        return_value=_response(200, _BUDGET_RESPONSE),
    ) as send:
        result = service.adjust_budget("demo-project", "CHG-2", request)

    assert send.call_args.args[0] == "PATCH"
    assert json.loads(send.call_args.kwargs["data"]) == {
        "amounts": {"cli": 0.0},
        "project": {},
    }
    assert result.status_code == 200


def test_cancel_budget_sends_delete_without_body_and_returns_no_budget(service):
    with patch(
        "codemie_sdk.services.provisioning.requests.request",
        return_value=_response(204),
    ) as send:
        result = service.cancel_budget("demo-project", "CHG-3")

    assert send.call_args.args[0] == "DELETE"
    assert send.call_args.kwargs["data"] is None
    assert (result.status_code, result.budget) == (204, None)


def test_missing_change_reference_leaves_the_header_out_and_empty_one_is_sent(service):
    with patch(
        "codemie_sdk.services.provisioning.requests.request",
        return_value=_response(204),
    ) as send:
        service.cancel_budget("demo-project", None)
        without_header = send.call_args.kwargs["headers"]
        service.cancel_budget("demo-project", "")
        empty_header = send.call_args.kwargs["headers"]

    assert "X-Change-Reference" not in without_header
    assert empty_header["X-Change-Reference"] == ""


def test_project_name_is_url_encoded(service):
    with patch(
        "codemie_sdk.services.provisioning.requests.request",
        return_value=_response(204),
    ) as send:
        service.cancel_budget("someone@example.com", "CHG-4")

    assert send.call_args.args[1] == f"{_BASE}/someone%40example.com/budget"


def test_request_sends_unknown_fields_and_non_finite_amounts_as_given(service):
    request = ProvisioningBudgetRequest(
        amounts={"platform": float("nan")}, unexpected_field=1
    )
    with patch(
        "codemie_sdk.services.provisioning.requests.request",
        return_value=_response(201, _BUDGET_RESPONSE),
    ) as send:
        service.set_budget("demo-project", "CHG-5", request)

    sent = send.call_args.kwargs["data"].replace(" ", "")
    assert '"unexpected_field":1' in sent
    assert '"platform":NaN' in sent


def test_http_error_is_raised_with_the_response(service):
    rejected = _response(403, {"detail": "no"})
    rejected.raise_for_status.side_effect = requests.HTTPError(response=rejected)
    with patch(
        "codemie_sdk.services.provisioning.requests.request", return_value=rejected
    ):
        with pytest.raises(requests.HTTPError) as error:
            service.cancel_budget("demo-project", "CHG-6")

    assert error.value.response.status_code == 403


def test_with_token_authenticates_with_the_new_token_and_leaves_the_original(service):
    other = service.with_token("client-token")
    with patch(
        "codemie_sdk.services.provisioning.requests.request",
        return_value=_response(204),
    ) as send:
        other.cancel_budget("demo-project", "CHG-7")
        assert send.call_args.kwargs["headers"]["Authorization"] == (
            "Bearer client-token"
        )
        service.cancel_budget("demo-project", "CHG-7")
        assert send.call_args.kwargs["headers"]["Authorization"] == "Bearer token"
