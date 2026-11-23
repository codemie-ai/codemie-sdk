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

"""Tests for WorkflowService.list_versions()/rollback(), mirroring the DummyApi
pattern used for AssistantService's own version endpoints in
``test_assistant_versions.py``.
"""

from types import SimpleNamespace

from codemie_sdk.services.workflow import WorkflowService


class DummyApi:
    def __init__(self, post_response: dict):
        self.last_call = SimpleNamespace(endpoint=None, params=None, json_data=None)
        self._post_response = post_response

    def get(self, endpoint, response_model, params=None, wrap_response=True):
        self.last_call.endpoint = endpoint
        self.last_call.params = params or {}
        raw = {
            "revisions": [],
            "total_revisions": 0,
            "workflow_name": "wf",
            "workflow_id": "workflow-123",
        }
        if response_model is dict:
            return raw
        return response_model.model_validate(raw)

    def post(
        self, endpoint, response_model, json_data=None, wrap_response=True, **kwargs
    ):
        self.last_call.endpoint = endpoint
        self.last_call.json_data = json_data or {}
        return self._post_response


def test_list_versions_calls_correct_endpoint():
    service = WorkflowService("https://api.example.com", "token")
    dummy_api = DummyApi(post_response={})
    service._api = dummy_api

    res = service.list_versions("workflow-123", page=1, per_page=5)

    assert dummy_api.last_call.endpoint == "/v1/workflows/workflow-123/versions"
    assert dummy_api.last_call.params == {"page": 1, "per_page": 5}
    assert res.total_revisions == 0
    assert res.workflow_id == "workflow-123"


def test_rollback_normalizes_camelcase_disabled_mcp_servers_key():
    """The backend's wrapper model serializes with ``alias_generator=to_camel``, so
    the raw response carries ``disabledMcpServers``; rollback() must normalize that
    back to ``disabled_mcp_servers`` while leaving each entry's own fields (already
    snake_case) untouched.
    """
    service = WorkflowService("https://api.example.com", "token")
    dummy_api = DummyApi(
        post_response={
            "message": "Workflow workflow-123 rolled back to revision 0.",
            "disabledMcpServers": [
                {
                    "name": "srv",
                    "mcp_config_id": "cfg-1",
                    "reason": "missing",
                    "address": None,
                }
            ],
        }
    )
    service._api = dummy_api

    res = service.rollback("workflow-123", 0)

    assert (
        dummy_api.last_call.endpoint == "/v1/workflows/workflow-123/versions/rollback"
    )
    assert dummy_api.last_call.json_data == {"revision_index": 0}
    assert isinstance(res, dict)
    assert res["message"] == "Workflow workflow-123 rolled back to revision 0."
    assert res["disabled_mcp_servers"] == [
        {"name": "srv", "mcp_config_id": "cfg-1", "reason": "missing", "address": None}
    ]


def test_rollback_defaults_disabled_mcp_servers_to_empty_list():
    service = WorkflowService("https://api.example.com", "token")
    dummy_api = DummyApi(
        post_response={
            "message": "Workflow workflow-123 rolled back to revision 0.",
            "disabledMcpServers": [],
        }
    )
    service._api = dummy_api

    res = service.rollback("workflow-123", 0, change_notes="manual rollback")

    assert dummy_api.last_call.json_data == {
        "revision_index": 0,
        "change_notes": "manual rollback",
    }
    assert res["disabled_mcp_servers"] == []
