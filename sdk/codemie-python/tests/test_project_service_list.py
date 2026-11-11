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

"""Unit tests for the query ProjectService.list_projects sends."""

from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from codemie_sdk.services.project import ProjectService

_FIRST = UUID("5f0c3a52-8d51-4b7b-9a53-2f7a6d1f2c11")
_SECOND = UUID("0b6f1c2e-3d4a-4f5b-8c6d-7e8f9a0b1c2d")
_EMPTY_PAGE = {"data": [], "pagination": {"total": 0, "page": 0, "per_page": 20}}


@pytest.fixture
def service():
    return ProjectService("https://api.example.com", "token")


def _list(service, **kwargs) -> dict:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = _EMPTY_PAGE
    with patch("codemie_sdk.utils.http.requests.get", return_value=response) as get:
        service.list_projects(**kwargs)
    return get.call_args.kwargs["params"]


def test_cost_center_ids_are_sent_as_a_list_of_strings(service):
    params = _list(service, cost_center_ids=[_FIRST, _SECOND])

    assert params["cost_center_ids"] == [str(_FIRST), str(_SECOND)]


@pytest.mark.parametrize("empty", [None, []], ids=["none", "empty list"])
def test_cost_center_ids_are_omitted_when_empty(service, empty):
    params = _list(service, cost_center_ids=empty)

    assert "cost_center_ids" not in params
