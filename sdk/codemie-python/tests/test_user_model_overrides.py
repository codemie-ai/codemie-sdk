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

"""Unit tests for the user model override methods of ProjectService."""

import json
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from codemie_sdk.services.project import ProjectService

_OVERRIDE = {
    "id": "6f1c1c1e-3a52-4a52-9d0e-1f6d6f1f0a11",
    "user_id": "user-1",
    "project_name": "p",
    "allowed_models": ["model-a", "model-b"],
    "default_model": "model-a",
    "date": "2026-01-01T00:00:00",
    "update_date": None,
}


@pytest.fixture
def service():
    return ProjectService("https://api.example.com", "token")


def _response(payload, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.content = json.dumps(payload).encode() if payload is not None else b""
    response.json.return_value = payload
    return response


def test_set_user_model_override_puts_the_models(service):
    with patch(
        "codemie_sdk.utils.http.requests.put", return_value=_response(_OVERRIDE)
    ) as put_req:
        result = service.set_user_model_override(
            "p", "user-1", ["model-a", "model-b"], default_model="model-a"
        )

    assert put_req.call_args.kwargs["url"].endswith(
        "/v1/projects/p/user-model-overrides/user-1"
    )
    assert put_req.call_args.kwargs["json"] == {
        "allowed_models": ["model-a", "model-b"],
        "default_model": "model-a",
    }
    assert result.user_id == "user-1"
    assert result.allowed_models == ["model-a", "model-b"]
    assert result.default_model == "model-a"


def test_set_user_model_override_omits_a_default_that_is_not_passed(service):
    with patch(
        "codemie_sdk.utils.http.requests.put", return_value=_response(_OVERRIDE)
    ) as put_req:
        service.set_user_model_override("p", "user-1", ["model-a"])

    assert put_req.call_args.kwargs["json"] == {"allowed_models": ["model-a"]}


def test_get_user_model_override_reads_one_override(service):
    with patch(
        "codemie_sdk.utils.http.requests.get", return_value=_response(_OVERRIDE)
    ) as get_req:
        result = service.get_user_model_override("p", "user-1")

    assert get_req.call_args.kwargs["url"].endswith(
        "/v1/projects/p/user-model-overrides/user-1"
    )
    assert result.project_name == "p"


def test_list_user_model_overrides_pages_the_project_overrides(service):
    with patch(
        "codemie_sdk.utils.http.requests.get", return_value=_response([_OVERRIDE])
    ) as get_req:
        result = service.list_user_model_overrides("p", skip=5, limit=10)

    assert get_req.call_args.kwargs["url"].endswith(
        "/v1/projects/p/user-model-overrides"
    )
    assert get_req.call_args.kwargs["params"] == {"skip": 5, "limit": 10}
    assert [o.user_id for o in result] == ["user-1"]


def test_delete_user_model_override_deletes_one_override(service):
    with patch(
        "codemie_sdk.utils.http.requests.delete",
        return_value=_response(None, status_code=204),
    ) as delete_req:
        result = service.delete_user_model_override("p", "user-1")

    assert delete_req.call_args.kwargs["url"].endswith(
        "/v1/projects/p/user-model-overrides/user-1"
    )
    assert result is None


def test_delete_user_model_override_ignores_a_json_body(service):
    with patch(
        "codemie_sdk.utils.http.requests.delete",
        return_value=_response({"message": "deleted"}),
    ):
        result = service.delete_user_model_override("p", "user-1")

    assert result is None


def test_user_model_override_dates_are_parsed_as_datetimes(service):
    with patch(
        "codemie_sdk.utils.http.requests.put",
        return_value=_response({**_OVERRIDE, "update_date": "2026-01-02T00:00:00"}),
    ):
        result = service.set_user_model_override("p", "user-1", ["model-a"])

    assert result.update_date - result.date == timedelta(days=1)


def test_batch_user_model_overrides_grants_to_every_user(service):
    with patch(
        "codemie_sdk.utils.http.requests.post",
        return_value=_response([_OVERRIDE, {**_OVERRIDE, "user_id": "user-2"}]),
    ) as post_req:
        result = service.batch_user_model_overrides(
            "p", "grant", ["user-1", "user-2"], ["model-a", "model-b"], "model-a"
        )

    assert post_req.call_args.kwargs["url"].endswith(
        "/v1/projects/p/user-model-overrides/batch"
    )
    assert post_req.call_args.kwargs["json"] == {
        "operation": "grant",
        "user_ids": ["user-1", "user-2"],
        "allowed_models": ["model-a", "model-b"],
        "default_model": "model-a",
    }
    assert [o.user_id for o in result] == ["user-1", "user-2"]


def test_batch_user_model_overrides_revoke_sends_no_models(service):
    with patch(
        "codemie_sdk.utils.http.requests.post", return_value=_response([_OVERRIDE])
    ) as post_req:
        service.batch_user_model_overrides("p", "revoke", ["user-1"])

    assert post_req.call_args.kwargs["json"] == {
        "operation": "revoke",
        "user_ids": ["user-1"],
    }
