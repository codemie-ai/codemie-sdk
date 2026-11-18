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

"""Unit tests for the admin LLM model status and global default calls."""

from unittest.mock import MagicMock, patch

import pytest

from codemie_sdk.models.admin import (
    AdminLLMModel,
    GlobalDefaultLLMModel,
    LLMModelStatusBulkItem,
    LLMModelStatusBulkResult,
    LLMModelStatusUpdate,
)
from codemie_sdk.models.assistant import Assistant
from codemie_sdk.models.llm import LLMModel, ModelStatus
from codemie_sdk.services.admin import AdminService

_ADMIN_MODEL = {
    "base_name": "model-a",
    "label": "Model A",
    "model_type": "chat",
    "enabled": True,
    "status": "deprecated",
    "provider": "azure_openai",
    "router_type": None,
    "is_premium": False,
    "cost": {"input": 0.000002, "output": 0.000008},
    "updated_by_name": "Admin",
    "updated_at": "2026-11-16T10:00:00Z",
}

_DEFAULT = {
    "saved_base_name": "model-a",
    "updated_by_id": "admin-1",
    "updated_by_name": "Admin",
    "updated_at": "2026-11-16T10:00:00Z",
    "effective_base_name": "model-a",
    "source": "admin",
    "temporary_fallback": False,
}


def _ok(body: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.content = b"{}"
    response.json.return_value = body
    return response


@pytest.fixture
def service():
    return AdminService("https://api.example.com", "token")


class TestListStatuses:
    def test_reads_models_from_the_data_wrapper(self, service):
        body = {"message": "ok", "data": [_ADMIN_MODEL]}
        with patch("codemie_sdk.utils.http.requests.get") as get:
            get.return_value = _ok(body)
            result = service.list_llm_model_statuses()

        assert get.call_args.kwargs["url"].endswith("/v1/admin/llm/status")
        assert len(result) == 1
        assert isinstance(result[0], AdminLLMModel)
        assert result[0].status == ModelStatus.DEPRECATED
        assert result[0].cost.output == 0.000008

    def test_ignores_fields_it_does_not_know(self, service):
        body = {"data": [{**_ADMIN_MODEL, "something_new": 1}]}
        with patch("codemie_sdk.utils.http.requests.get") as get:
            get.return_value = _ok(body)
            result = service.list_llm_model_statuses()

        assert result[0].base_name == "model-a"


class TestSetStatus:
    def test_puts_status_to_the_model_path(self, service):
        body = {"message": "ok", "data": {"base_name": "model-a", "status": "disabled"}}
        with patch("codemie_sdk.utils.http.requests.put") as put:
            put.return_value = _ok(body)
            result = service.set_llm_model_status("model-a", ModelStatus.DISABLED)

        assert put.call_args.kwargs["url"].endswith("/v1/admin/llm/model-a/status")
        assert put.call_args.kwargs["json"] == {"status": "disabled"}
        assert isinstance(result, LLMModelStatusUpdate)
        assert result.status == ModelStatus.DISABLED

    def test_accepts_the_status_as_a_string(self, service):
        body = {"data": {"base_name": "model-a", "status": "enabled"}}
        with patch("codemie_sdk.utils.http.requests.put") as put:
            put.return_value = _ok(body)
            service.set_llm_model_status("model-a", "enabled")

        assert put.call_args.kwargs["json"] == {"status": "enabled"}

    def test_encodes_the_base_name_in_the_path(self, service):
        body = {"data": {"base_name": "a/b", "status": "enabled"}}
        with patch("codemie_sdk.utils.http.requests.put") as put:
            put.return_value = _ok(body)
            service.set_llm_model_status("a/b", ModelStatus.ENABLED)

        assert put.call_args.kwargs["url"].endswith("/v1/admin/llm/a%2Fb/status")

    def test_rejects_an_unknown_status_before_sending(self, service):
        with patch("codemie_sdk.utils.http.requests.put") as put:
            with pytest.raises(ValueError):
                service.set_llm_model_status("model-a", "retired")

        put.assert_not_called()


class TestBulkSetStatuses:
    def test_posts_updates_and_returns_per_item_results(self, service):
        body = {
            "message": "done",
            "data": {
                "total": 2,
                "succeeded": 1,
                "failed": 1,
                "results": [
                    {
                        "base_name": "model-a",
                        "status": "disabled",
                        "success": True,
                        "error": None,
                    },
                    {
                        "base_name": "missing",
                        "status": "disabled",
                        "success": False,
                        "error": "Model 'missing' was not found in the current catalog.",
                    },
                ],
            },
        }
        updates = [
            LLMModelStatusBulkItem(base_name="model-a", status=ModelStatus.DISABLED),
            LLMModelStatusBulkItem(base_name="missing", status=ModelStatus.DISABLED),
        ]
        with patch("codemie_sdk.utils.http.requests.post") as post:
            post.return_value = _ok(body)
            result = service.bulk_set_llm_model_statuses(updates)

        assert post.call_args.kwargs["url"].endswith("/v1/admin/llm/status/bulk")
        assert post.call_args.kwargs["json"] == {
            "updates": [
                {"base_name": "model-a", "status": "disabled"},
                {"base_name": "missing", "status": "disabled"},
            ]
        }
        assert isinstance(result, LLMModelStatusBulkResult)
        assert (result.total, result.succeeded, result.failed) == (2, 1, 1)
        assert result.results[1].success is False
        assert "missing" in result.results[1].error


class TestGlobalDefault:
    def test_get_reads_the_unwrapped_body(self, service):
        with patch("codemie_sdk.utils.http.requests.get") as get:
            get.return_value = _ok(_DEFAULT)
            result = service.get_global_default_llm_model()

        assert get.call_args.kwargs["url"].endswith("/v1/admin/llm/default")
        assert isinstance(result, GlobalDefaultLLMModel)
        assert result.saved_base_name == "model-a"
        assert result.effective_base_name == "model-a"
        assert result.temporary_fallback is False

    def test_set_puts_the_base_name(self, service):
        with patch("codemie_sdk.utils.http.requests.put") as put:
            put.return_value = _ok(_DEFAULT)
            result = service.set_global_default_llm_model("model-a")

        assert put.call_args.kwargs["url"].endswith("/v1/admin/llm/default")
        assert put.call_args.kwargs["json"] == {"base_name": "model-a"}
        assert result.source == "admin"

    def test_reset_deletes_the_saved_default(self, service):
        cleared = {
            **_DEFAULT,
            "saved_base_name": None,
            "source": "config",
            "updated_by_id": None,
            "updated_by_name": None,
            "updated_at": None,
        }
        with patch("codemie_sdk.utils.http.requests.delete") as delete:
            delete.return_value = _ok(cleared)
            result = service.reset_global_default_llm_model()

        assert delete.call_args.kwargs["url"].endswith("/v1/admin/llm/default")
        assert result.saved_base_name is None

    def test_reset_reads_the_default_back_after_no_content(self, service):
        empty = MagicMock()
        empty.status_code = 204
        empty.content = b""
        with (
            patch("codemie_sdk.utils.http.requests.delete") as delete,
            patch("codemie_sdk.utils.http.requests.get") as get,
        ):
            delete.return_value = empty
            get.return_value = _ok({**_DEFAULT, "saved_base_name": None})
            result = service.reset_global_default_llm_model()

        assert get.call_args.kwargs["url"].endswith("/v1/admin/llm/default")
        assert isinstance(result, GlobalDefaultLLMModel)
        assert result.saved_base_name is None


class TestModelStatusFields:
    def test_llm_model_status_is_read_from_the_catalog(self):
        model = LLMModel.model_validate(
            {"base_name": "model-a", "enabled": True, "status": "deprecated"}
        )

        assert model.status == ModelStatus.DEPRECATED

    def test_llm_model_status_is_optional(self):
        model = LLMModel.model_validate({"base_name": "model-a", "enabled": True})

        assert model.status is None

    def test_assistant_detail_carries_the_effective_model_reason(self):
        assistant = Assistant.model_validate(
            {
                "name": "a",
                "description": "d",
                "system_prompt": "p",
                "project": "proj",
                "llm_model_type": "model-b",
                "effective_llm_model_reason": "The configured model is disabled. "
                "An available fallback is used.",
            }
        )

        assert assistant.effective_llm_model_reason.startswith(
            "The configured model is disabled"
        )

    def test_assistant_detail_reason_defaults_to_none(self):
        assistant = Assistant.model_validate(
            {"name": "a", "description": "d", "system_prompt": "p", "project": "proj"}
        )

        assert assistant.effective_llm_model_reason is None

    def test_unknown_catalog_status_does_not_break_parsing(self):
        model = LLMModel.model_validate(
            {"base_name": "model-a", "enabled": True, "status": "retired"}
        )

        assert model.status == "retired"

    def test_unknown_admin_status_does_not_break_parsing(self):
        model = AdminLLMModel.model_validate({**_ADMIN_MODEL, "status": "preview"})
        update = LLMModelStatusUpdate.model_validate(
            {"base_name": "model-a", "status": "preview"}
        )

        assert model.status == "preview"
        assert update.status == "preview"

    def test_known_status_is_still_an_enum(self):
        update = LLMModelStatusUpdate.model_validate(
            {"base_name": "model-a", "status": "enabled"}
        )

        assert update.status is ModelStatus.ENABLED

    def test_bulk_item_request_still_rejects_an_unknown_status(self):
        with pytest.raises(ValueError):
            LLMModelStatusBulkItem(base_name="model-a", status="preview")
