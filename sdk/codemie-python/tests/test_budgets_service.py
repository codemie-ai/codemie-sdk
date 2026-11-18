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

"""Unit tests for the budgets service: route, verb and error propagation."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from codemie_sdk.services.budgets import BudgetsService

_BASE = "https://api.example.com/v1/admin/budgets"


def _response(status: int, content: bytes = b"") -> MagicMock:
    response = MagicMock()
    response.status_code = status
    response.content = content
    if status >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(
            f"{status} error", response=response
        )
    return response


@pytest.fixture
def service() -> BudgetsService:
    return BudgetsService("https://api.example.com", "token")


def test_delete_sends_delete_to_the_budget_route_and_returns_the_response(service):
    raw = _response(204)
    with patch("codemie_sdk.utils.http.requests.request", return_value=raw) as request:
        result = service.delete("budget-1")

    assert request.call_args.kwargs["method"] == "DELETE"
    assert request.call_args.kwargs["url"] == f"{_BASE}/budget-1"
    assert result is raw
    assert result.status_code == 204
    assert result.content == b""


@pytest.mark.parametrize("status", [403, 404, 409, 502])
def test_delete_raises_http_error_carrying_the_response(service, status):
    body = b'{"error": {"message": "refused"}}'
    with patch(
        "codemie_sdk.utils.http.requests.request",
        return_value=_response(status, body),
    ):
        with pytest.raises(requests.HTTPError) as exc_info:
            service.delete("budget-1")

    assert exc_info.value.response.status_code == status
    assert exc_info.value.response.content == body


def test_delete_rejects_an_empty_budget_id(service):
    with pytest.raises(ValueError):
        service.delete("")
