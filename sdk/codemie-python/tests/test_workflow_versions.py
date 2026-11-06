import json
from datetime import datetime
from types import SimpleNamespace

import pytest
import requests
from pydantic import ValidationError

from codemie_sdk.services.workflow import WorkflowService
from codemie_sdk.models.workflow import (
    WorkflowRevisionCreatedBy,
    WorkflowVersionHistoryResponse,
)
from codemie_sdk.utils import ApiRequestHandler

# Raw GET /v1/workflows/{id}/versions body as the backend serializes it (not wrapped in "data").
VERSIONS_WIRE_PAYLOAD = {
    "revisions": [
        {
            "yaml_config": "steps: []",
            "date": "2026-08-27T10:00:00",
            "created_by": {"user_id": "u1", "username": "alice", "name": "Alice"},
            "change_notes": None,
        }
    ],
    "total_revisions": 1,
    "workflow_name": "My Workflow",
    "workflow_id": "wf-123",
}


def _json_response(payload):
    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps(payload).encode()
    return response


class DummyApi:
    """Records calls and parses the canned body through the real response parser."""

    def __init__(self, versions_payload=None):
        self._versions_payload = versions_payload or VERSIONS_WIRE_PAYLOAD
        self.last_call = SimpleNamespace(
            endpoint=None,
            params=None,
            json_data=None,
            response_model=None,
            wrap_response=None,
        )
        self._parser = ApiRequestHandler("https://api.example.com", "token")

    def get(self, endpoint, response_model, params=None, wrap_response=True):
        self.last_call.endpoint = endpoint
        self.last_call.params = params or {}
        self.last_call.response_model = response_model
        self.last_call.wrap_response = wrap_response
        return self._parser._parse_response(
            _json_response(self._versions_payload), response_model, wrap_response
        )

    def post(
        self, endpoint, response_model, json_data=None, stream=False, wrap_response=True
    ):
        self.last_call.endpoint = endpoint
        self.last_call.json_data = json_data or {}
        idx = (json_data or {}).get("revision_index", 0)
        return {"message": f"Workflow wf-123 rolled back to revision {idx}."}


def test_revision_created_by_parses_wire_user_id():
    created = WorkflowRevisionCreatedBy.model_validate(
        {"user_id": "u1", "username": "alice", "name": "Alice"}
    )

    assert created.user_id == "u1"
    assert created.username == "alice"
    assert created.name == "Alice"


def test_list_versions_calls_correct_endpoint():
    service = WorkflowService("https://api.example.com", "token")
    dummy = DummyApi()
    service._api = dummy

    result = service.list_versions("wf-123")

    assert dummy.last_call.endpoint == "/v1/workflows/wf-123/versions"
    assert dummy.last_call.response_model is WorkflowVersionHistoryResponse
    assert dummy.last_call.wrap_response is False
    assert isinstance(result, WorkflowVersionHistoryResponse)
    assert result.workflow_id == "wf-123"
    assert result.workflow_name == "My Workflow"
    assert result.total_revisions == 1
    assert len(result.revisions) == 1


def test_list_versions_parses_wire_revision_fields():
    service = WorkflowService("https://api.example.com", "token")
    service._api = DummyApi()

    revision = service.list_versions("wf-123").revisions[0]

    assert revision.yaml_config == "steps: []"
    assert revision.date == datetime(2026, 8, 27, 10, 0, 0)
    assert isinstance(revision.created_by, WorkflowRevisionCreatedBy)
    assert revision.created_by.user_id == "u1"
    assert revision.created_by.username == "alice"
    assert revision.created_by.name == "Alice"
    assert revision.change_notes is None


def test_list_versions_accepts_revision_without_creator():
    # Backend declares YamlConfigHistory.created_by as Optional[UserEntity] = None.
    payload = {
        **VERSIONS_WIRE_PAYLOAD,
        "revisions": [
            {**VERSIONS_WIRE_PAYLOAD["revisions"][0], "created_by": None},
            VERSIONS_WIRE_PAYLOAD["revisions"][0],
        ],
        "total_revisions": 2,
    }
    service = WorkflowService("https://api.example.com", "token")
    service._api = DummyApi(payload)

    result = service.list_versions("wf-123")

    assert result.revisions[0].created_by is None
    assert result.revisions[1].created_by.user_id == "u1"


def test_rollback_rejects_negative_revision_index():
    service = WorkflowService("https://api.example.com", "token")
    dummy = DummyApi()
    service._api = dummy

    with pytest.raises(ValidationError):
        service.rollback("wf-123", -1)

    assert dummy.last_call.endpoint is None


def test_rollback_calls_correct_endpoint():
    service = WorkflowService("https://api.example.com", "token")
    dummy = DummyApi()
    service._api = dummy

    result = service.rollback("wf-123", 0)

    assert dummy.last_call.endpoint == "/v1/workflows/wf-123/versions/rollback"
    assert dummy.last_call.json_data["revision_index"] == 0
    assert "change_notes" not in dummy.last_call.json_data
    assert "rolled back" in result["message"]


def test_rollback_includes_change_notes_when_provided():
    service = WorkflowService("https://api.example.com", "token")
    dummy = DummyApi()
    service._api = dummy

    service.rollback("wf-123", 2, change_notes="Reverting bad config")

    assert dummy.last_call.json_data["revision_index"] == 2
    assert dummy.last_call.json_data["change_notes"] == "Reverting bad config"


def test_rollback_omits_change_notes_when_none():
    service = WorkflowService("https://api.example.com", "token")
    dummy = DummyApi()
    service._api = dummy

    service.rollback("wf-123", 1)

    assert "change_notes" not in dummy.last_call.json_data
