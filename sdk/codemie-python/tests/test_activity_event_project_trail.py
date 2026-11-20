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

"""Unit tests for the project-scoped activity trail methods."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from codemie_sdk.models.activity_event import (
    ActivityEventListItem,
    ActivityEventProjectMetadata,
    ProjectActivityEventsResponse,
)
from codemie_sdk.services.activity_event import ActivityEventService

_ITEM = {
    "id": "e1",
    "domain": "project_management",
    "event_type": "project.created",
    "label": "Project Created",
    "category": "Settings",
    "entity_type": "project",
    "entity_id": "p",
    "entity_label": "P",
    "project_name": "p",
    "actor_id": None,
    "actor_email": "a@example.com",
    "actor_name": "A",
    "attributes": None,
    "created_at": "2026-01-01T00:00:00Z",
}


@pytest.fixture
def service():
    return ActivityEventService("https://api.example.com", "token")


def _response(payload):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = payload
    return response


def test_list_item_keeps_label_category_entity_label_and_project_name():
    item = ActivityEventListItem(**_ITEM)
    assert (item.label, item.category, item.entity_label, item.project_name) == (
        "Project Created",
        "Settings",
        "P",
        "p",
    )


def test_list_item_without_new_fields_still_parses():
    legacy = {k: v for k, v in _ITEM.items() if k not in ("label", "category")}
    item = ActivityEventListItem(**legacy)
    assert item.label is None
    assert item.category is None


def test_list_project_events_builds_request_and_parses_response(service):
    project_id = uuid4()
    payload = {
        "data": [_ITEM],
        "pagination": {"page": 0, "per_page": 2, "total": 1, "pages": 1},
        "recording_enabled": True,
    }
    with patch(
        "codemie_sdk.utils.http.requests.get", return_value=_response(payload)
    ) as get:
        result = service.list_project_events(
            project_id,
            category=["Budget"],
            domain=["project_management"],
            from_dt="2026-01-01T00:00:00Z",
            sort_dir="asc",
            limit=2,
            offset=2,
        )

    assert isinstance(result, ProjectActivityEventsResponse)
    assert result.recording_enabled is True
    assert result.data[0].project_name == "p"
    kwargs = get.call_args.kwargs
    assert kwargs["url"].endswith(f"/v1/projects/{project_id}/activity-events")
    assert kwargs["params"] == {
        "category": ["Budget"],
        "domain": ["project_management"],
        "from": "2026-01-01T00:00:00Z",
        "sort_dir": "asc",
        "limit": 2,
        "offset": 2,
    }


def test_list_project_events_sends_no_params_by_default(service):
    payload = {
        "data": [],
        "pagination": {"page": 0, "per_page": 50, "total": 0, "pages": 0},
        "recording_enabled": False,
    }
    with patch(
        "codemie_sdk.utils.http.requests.get", return_value=_response(payload)
    ) as get:
        service.list_project_events("abc")
    assert get.call_args.kwargs["params"] is None


def test_get_project_event_metadata_parses_response(service):
    payload = {
        "domains": ["project_management"],
        "event_types": [
            {
                "event_type": "project.created",
                "label": "Project Created",
                "category": "Settings",
            }
        ],
        "categories": ["Budget", "Members", "Settings", "Account"],
        "recording_enabled": True,
    }
    with patch(
        "codemie_sdk.utils.http.requests.get", return_value=_response(payload)
    ) as get:
        result = service.get_project_event_metadata("abc")

    assert isinstance(result, ActivityEventProjectMetadata)
    assert result.event_types[0].category == "Settings"
    assert get.call_args.kwargs["url"].endswith(
        "/v1/projects/abc/activity-events/metadata"
    )
