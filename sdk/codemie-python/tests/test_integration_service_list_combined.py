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

"""Unit tests for the query and response of IntegrationService.list_combined."""

import json
from unittest.mock import MagicMock, patch

import pytest

from codemie_sdk.models.integration import IntegrationType
from codemie_sdk.services.integration import IntegrationService

_ROW = {
    "id": "row-1",
    "project_name": "demo",
    "alias": "demo-alias",
    "credential_type": "Jira",
    "credential_values": [{"key": "url", "value": "https://example.invalid"}],
    "setting_type": "project",
    "is_global": False,
}
_PAGE = {
    "data": [_ROW],
    "pagination": {"page": 0, "per_page": 10, "total": 1, "pages": 1},
}


@pytest.fixture
def service():
    return IntegrationService("https://api.example.com", "token")


def _call(service, **kwargs):
    response = MagicMock()
    response.status_code = 200
    response.content = b"{}"
    response.json.return_value = _PAGE
    with patch("codemie_sdk.utils.http.requests.get", return_value=response) as get:
        result = service.list_combined(**kwargs)
    return result, get.call_args


def test_default_call_sends_scope_all_and_first_page(service):
    _, call = _call(service)

    assert call.kwargs["url"] == "https://api.example.com/v1/settings"
    assert call.kwargs["params"] == {"page": 0, "per_page": 10, "scope": "all"}


def test_scope_none_omits_the_parameter(service):
    _, call = _call(service, scope=None)

    assert "scope" not in call.kwargs["params"]


@pytest.mark.parametrize("scope", ["user", "project", "team"])
def test_scope_is_sent_unchanged(service, scope):
    _, call = _call(service, scope=scope)

    assert call.kwargs["params"]["scope"] == scope


@pytest.mark.parametrize("per_page", [0, 101])
def test_out_of_range_paging_is_not_checked_client_side(service, per_page):
    _, call = _call(service, per_page=per_page)

    assert call.kwargs["params"]["per_page"] == per_page


def test_dict_filters_are_sent_as_json(service):
    _, call = _call(service, filters={"search": "jira", "is_global": True})

    assert json.loads(call.kwargs["params"]["filters"]) == {
        "search": "jira",
        "is_global": True,
    }


def test_string_filters_are_sent_unchanged(service):
    _, call = _call(service, filters="{not json")

    assert call.kwargs["params"]["filters"] == "{not json"


def test_response_keeps_rows_and_pagination(service):
    result, _ = _call(service)

    assert [row.id for row in result.data] == ["row-1"]
    assert result.data[0].setting_type == IntegrationType.PROJECT
    assert result.pagination.total == 1
    assert result.pagination.pages == 1
