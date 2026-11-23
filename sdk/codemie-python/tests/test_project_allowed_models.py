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

"""Unit tests for the project model settings methods of ProjectService."""

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from codemie_sdk.models.project import ProjectDetailResponse
from codemie_sdk.services.project import ProjectService

_SETTINGS = dict(
    name="p",
    description="d",
    project_type="shared",
    created_by="u",
    created_at=datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
    allowed_models=["model-a", "model-b"],
    default_model="model-a",
)


@pytest.fixture
def service():
    return ProjectService("https://api.example.com", "token")


def _response(payload):
    response = MagicMock()
    response.status_code = 200
    response.content = json.dumps(payload).encode()
    response.json.return_value = payload
    return response


def test_update_allowed_models_patches_both_fields(service):
    with patch(
        "codemie_sdk.utils.http.requests.patch", return_value=_response(_SETTINGS)
    ) as patch_req:
        result = service.update_allowed_models(
            "p", allowed_models=["model-a", "model-b"], default_model="model-a"
        )

    assert patch_req.call_args.kwargs["url"].endswith("/v1/projects/p/allowed-models")
    assert patch_req.call_args.kwargs["json"] == {
        "allowed_models": ["model-a", "model-b"],
        "default_model": "model-a",
    }
    assert result.allowed_models == ["model-a", "model-b"]
    assert result.default_model == "model-a"


def test_update_allowed_models_omits_fields_that_are_not_passed(service):
    with patch(
        "codemie_sdk.utils.http.requests.patch", return_value=_response(_SETTINGS)
    ) as patch_req:
        service.update_allowed_models("p", default_model="model-b")

    assert patch_req.call_args.kwargs["json"] == {"default_model": "model-b"}


def test_reset_allowed_models_deletes_the_settings(service):
    cleared = {**_SETTINGS, "allowed_models": None, "default_model": None}
    with patch(
        "codemie_sdk.utils.http.requests.delete", return_value=_response(cleared)
    ) as delete_req:
        result = service.reset_allowed_models("p")

    assert delete_req.call_args.kwargs["url"].endswith("/v1/projects/p/allowed-models")
    assert result.allowed_models is None
    assert result.default_model is None


def test_project_detail_exposes_the_model_settings():
    detail = ProjectDetailResponse(
        name="p",
        project_type="shared",
        user_count=1,
        admin_count=1,
        members=[],
        allowed_models=None,
        default_model="model-a",
    )

    assert detail.allowed_models is None
    assert detail.default_model == "model-a"


def test_project_detail_defaults_the_model_settings_to_none():
    detail = ProjectDetailResponse(
        name="p", project_type="shared", user_count=1, admin_count=1, members=[]
    )

    assert detail.allowed_models is None
    assert detail.default_model is None
