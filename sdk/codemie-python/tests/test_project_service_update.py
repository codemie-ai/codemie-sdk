"""Unit tests for the payload ProjectService.update_project sends."""

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from codemie_sdk.services.project import ProjectService

_COST_CENTER_ID = UUID("5f0c3a52-8d51-4b7b-9a53-2f7a6d1f2c11")
_UPDATED = dict(
    name="p",
    project_type="shared",
    created_by="u",
    created_at=datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
)


@pytest.fixture
def service():
    return ProjectService("https://api.example.com", "token")


def test_update_project_sends_json_serialisable_cost_center_id(service):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = _UPDATED
    with patch(
        "codemie_sdk.utils.http.requests.patch", return_value=response
    ) as patch_req:
        service.update_project("p", cost_center_id=_COST_CENTER_ID)

    sent = patch_req.call_args.kwargs["json"]
    assert json.loads(json.dumps(sent))["cost_center_id"] == str(_COST_CENTER_ID)
