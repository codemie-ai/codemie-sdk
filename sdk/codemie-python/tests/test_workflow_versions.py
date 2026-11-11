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

"""Tests for WorkflowService.list_versions() and rollback().

The network layer is faked one layer down, at the service's ``_api``, so the
real method bodies still run.
"""

import pytest
from pydantic import ValidationError

from codemie_sdk.models.workflow import (
    WorkflowRevision,
    WorkflowVersionHistoryResponse,
)
from codemie_sdk.services.workflow import WorkflowService


class _FakeApi:
    """Minimal ApiRequestHandler stand-in that records get/post calls."""

    def __init__(self):
        self.get_calls: list[tuple] = []
        self.post_calls: list[tuple] = []

    def get(self, endpoint, response_model, params=None, wrap_response=True):
        self.get_calls.append((endpoint, response_model, params, wrap_response))
        return WorkflowVersionHistoryResponse(
            revisions=[
                WorkflowRevision(
                    revision_index=2,
                    yaml_config="a: 1",
                    date="2026-01-01T00:00:00",
                    created_by={"id": "u-1", "username": "user", "name": "User"},
                    change_notes="note",
                )
            ],
            total_revisions=3,
            workflow_name="wf",
            workflow_id="wf-1",
        )

    def post(self, endpoint, response_model, json_data=None, wrap_response=True):
        self.post_calls.append((endpoint, response_model, json_data, wrap_response))
        return {"message": "Workflow wf-1 rolled back to revision 1."}


def _service() -> tuple[WorkflowService, _FakeApi]:
    service = WorkflowService("https://api.example.com", "token")
    api = _FakeApi()
    service._api = api
    return service, api


def test_list_versions_without_paging_sends_no_params():
    service, api = _service()

    result = service.list_versions("wf-1")

    endpoint, model, params, wrap = api.get_calls[0]
    assert endpoint == "/v1/workflows/wf-1/versions"
    assert model is WorkflowVersionHistoryResponse
    assert params is None
    assert wrap is False
    assert result.total_revisions == 3
    assert result.revisions[0].revision_index == 2


def test_list_versions_sends_page_and_per_page_unvalidated():
    service, api = _service()

    service.list_versions("wf-1", page=-1, per_page=101)

    assert api.get_calls[0][2] == {"page": -1, "per_page": 101}


def test_list_versions_keeps_zero_page():
    service, api = _service()

    service.list_versions("wf-1", page=0)

    assert api.get_calls[0][2] == {"page": 0}


def test_rollback_posts_revision_index_and_change_notes():
    service, api = _service()

    result = service.rollback("wf-1", 1, change_notes="restore")

    endpoint, model, body, _ = api.post_calls[0]
    assert endpoint == "/v1/workflows/wf-1/versions/rollback"
    assert model is dict
    assert body == {"revision_index": 1, "change_notes": "restore"}
    assert result == {"message": "Workflow wf-1 rolled back to revision 1."}


def test_rollback_omits_absent_change_notes():
    service, api = _service()

    service.rollback("wf-1", 0)

    assert api.post_calls[0][2] == {"revision_index": 0}


def test_rollback_rejects_negative_revision_index_client_side():
    service, api = _service()

    with pytest.raises(ValidationError):
        service.rollback("wf-1", -1)

    assert api.post_calls == []


def test_revision_model_parses_backend_payload():
    revision = WorkflowRevision.model_validate(
        {
            "revision_index": 4,
            "yaml_config": "a: 1",
            "date": "2026-01-01T00:00:00",
            "created_by": {"user_id": "u-1", "username": "user", "name": "User"},
            "change_notes": None,
            "extra_field": "ignored",
        }
    )

    assert revision.revision_index == 4
    assert revision.created_by.user_id == "u-1"
    assert revision.change_notes is None
