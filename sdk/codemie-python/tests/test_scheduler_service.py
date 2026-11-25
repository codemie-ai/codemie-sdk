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

"""Unit tests for SchedulerService."""

from unittest.mock import MagicMock, patch

from codemie_sdk.services.scheduler import SchedulerService

_BODY = {
    "items": [
        {
            "id": "scheduler-1",
            "name": "Nightly run",
            "resource": {"id": "assistant-1", "name": "Helper", "type": "Assistant"},
            "project": {"id": "demo", "name": "demo"},
            "schedule": {
                "cron": "0 * * * *",
                "description": "Every hour",
                "timezone": "UTC",
                "nextRunAt": "2026-01-01T01:00:00+00:00",
            },
            "isEnabled": False,
            "lastRun": None,
        }
    ],
    "pagination": {"page": 0, "per_page": 10, "total": 1, "pages": 1},
}


def _ok_response(body: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.content = b"{}"
    response.json.return_value = body
    return response


def _service() -> SchedulerService:
    return SchedulerService("https://api.example.com", "token")


def test_list_sends_api_parameter_names_and_omits_owner_type_by_default():
    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(_BODY)
        _service().list(page=2, per_page=50)

    kwargs = get.call_args.kwargs
    assert kwargs["url"] == "https://api.example.com/v1/schedulers"
    assert kwargs["params"] == {"page": 2, "pageSize": 50}


def test_list_sends_owner_type_when_given():
    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(_BODY)
        _service().list(owner_type="user")

    assert get.call_args.kwargs["params"] == {
        "page": 0,
        "pageSize": 10,
        "ownerType": "user",
    }


def test_list_parses_items_and_pagination():
    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(_BODY)
        result = _service().list()

    item = result.items[0]
    assert item.id == "scheduler-1"
    assert item.name == "Nightly run"
    assert item.resource.type == "Assistant"
    assert item.project.name == "demo"
    assert item.is_enabled is False
    assert item.schedule.next_run_at == "2026-01-01T01:00:00+00:00"
    assert item.last_run is None
    assert result.pagination.total == 1


def test_update_sends_is_enabled_and_parses_the_item():
    with patch("codemie_sdk.utils.http.requests.patch") as patch_req:
        patch_req.return_value = _ok_response(_BODY["items"][0])
        result = _service().update("scheduler-1", is_enabled=False)

    kwargs = patch_req.call_args.kwargs
    assert kwargs["url"] == "https://api.example.com/v1/schedulers/scheduler-1"
    assert kwargs["json"] == {"isEnabled": False}
    assert result.id == "scheduler-1"
    assert result.is_enabled is False
