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

"""Tests for WorkflowBuilder.publish()'s create/update dispatch and name resolution.

Fakes are installed one layer down, at each Service's ``_api`` (the
``Service.__new__(Service)`` + fake ``_api`` pattern from
``test_chat_with_version.py``), so the real ``WorkflowService``/
``AssistantService`` method bodies still run and only the network layer is
faked.
"""

import requests
import pytest

from codemie_sdk.client.client import CodeMieClient
from codemie_sdk.models.assistant import Assistant
from codemie_sdk.models.workflow import WorkflowMode
from codemie_sdk.services.assistant import AssistantService
from codemie_sdk.services.workflow import WorkflowService
from codemie_sdk.builders.workflow.builder import WorkflowBuilder


class _FakeWorkflowsApi:
    """Minimal ApiRequestHandler stand-in that records post/put calls."""

    def __init__(self, post_error: Exception | None = None):
        self.post_calls: list[tuple[str, dict]] = []
        self.put_calls: list[tuple[str, dict]] = []
        self._post_error = post_error

    def post(self, endpoint, response_model, json_data=None):
        if self._post_error is not None:
            raise self._post_error
        self.post_calls.append((endpoint, json_data))
        return {"id": "wf-1", **json_data}

    def put(self, endpoint, response_model, json_data=None):
        self.put_calls.append((endpoint, json_data))
        return {"id": "wf-1", **json_data}


class _FakeAssistantsApi:
    """Minimal ApiRequestHandler stand-in that records and paginates get() calls."""

    def __init__(self, assistants: list[Assistant]):
        self._assistants = assistants
        self.get_calls = 0
        self.list_params: list[dict] = []

    def get(self, endpoint, response_model, params=None):
        self.get_calls += 1
        params = params or {}
        self.list_params.append(params)
        page = params.get("page", 0)
        per_page = params.get("per_page") or len(self._assistants) or 1
        start = page * per_page
        return self._assistants[start : start + per_page]


def _client_with(
    workflows_api: _FakeWorkflowsApi, assistants_api: _FakeAssistantsApi
) -> CodeMieClient:
    client = CodeMieClient.__new__(CodeMieClient)

    workflows = WorkflowService.__new__(WorkflowService)
    workflows._api = workflows_api
    client.workflows = workflows

    assistants = AssistantService.__new__(AssistantService)
    assistants._api = assistants_api
    client.assistants = assistants

    return client


def _basic_builder():
    return WorkflowBuilder("wf").with_mode(WorkflowMode.SEQUENTIAL)


def _assistant(name: str, assistant_id: str, project: str = "p") -> Assistant:
    return Assistant(
        id=assistant_id,
        name=name,
        description="d",
        system_prompt="s",
        project=project,
    )


def test_publish_create_no_workflow_id():
    workflows_api = _FakeWorkflowsApi()
    assistants_api = _FakeAssistantsApi([])
    client = _client_with(workflows_api, assistants_api)
    builder = _basic_builder()

    builder.publish(client, "proj1")

    assert len(workflows_api.post_calls) == 1
    endpoint, json_data = workflows_api.post_calls[0]
    assert endpoint == "/v1/workflows"
    assert json_data["yaml_config"] == builder.render().to_yaml_config()
    assert json_data["project"] == "proj1"
    assert json_data["name"] == "wf"
    assert workflows_api.put_calls == []


def test_publish_update_given_workflow_id():
    workflows_api = _FakeWorkflowsApi()
    assistants_api = _FakeAssistantsApi([])
    client = _client_with(workflows_api, assistants_api)
    builder = _basic_builder()

    builder.publish(client, "proj1", workflow_id="w1")

    assert workflows_api.post_calls == []
    assert len(workflows_api.put_calls) == 1
    endpoint, json_data = workflows_api.put_calls[0]
    assert endpoint == "/v1/workflows/w1"
    # WorkflowUpdateRequest.description is a required, non-empty string, so a
    # missing builder description is substituted with " " (not ""), which
    # still satisfies "no meaningful description supplied" while validating.
    assert json_data["description"] == " "


def test_publish_create_without_description_still_sends_one():
    """Regression: WorkflowCreateRequest.description is Optional in the SDK's
    own model, but the backend's CreateWorkflowRequest requires a non-empty
    str. Sending `None` would 422 before the create ever reaches the backend,
    so create must substitute the same " " placeholder update() already uses."""
    workflows_api = _FakeWorkflowsApi()
    assistants_api = _FakeAssistantsApi([])
    client = _client_with(workflows_api, assistants_api)
    builder = _basic_builder()

    builder.publish(client, "proj1")

    _, json_data = workflows_api.post_calls[0]
    assert json_data["description"] == " "


def test_publish_resolves_assistant_name():
    workflows_api = _FakeWorkflowsApi()
    assistants_api = _FakeAssistantsApi([_assistant("x", "asst-1")])
    client = _client_with(workflows_api, assistants_api)
    builder = (
        WorkflowBuilder("wf")
        .with_mode(WorkflowMode.SEQUENTIAL)
        .add_assistant_ref("a1", "x")
    )

    builder.publish(client, "p")

    _, json_data = workflows_api.post_calls[0]
    assert "assistant_id: asst-1" in json_data["yaml_config"]
    assert assistants_api.get_calls == 1


def test_publish_zero_matches_raises():
    workflows_api = _FakeWorkflowsApi()
    assistants_api = _FakeAssistantsApi([])
    client = _client_with(workflows_api, assistants_api)
    builder = (
        WorkflowBuilder("wf")
        .with_mode(WorkflowMode.SEQUENTIAL)
        .add_assistant_ref("a1", "x")
    )

    with pytest.raises(ValueError, match="x"):
        builder.publish(client, "p")


def test_publish_duplicate_matches_raises():
    workflows_api = _FakeWorkflowsApi()
    dup = [_assistant("x", "asst-1"), _assistant("x", "asst-2")]
    assistants_api = _FakeAssistantsApi(dup)
    client = _client_with(workflows_api, assistants_api)
    builder = (
        WorkflowBuilder("wf")
        .with_mode(WorkflowMode.SEQUENTIAL)
        .add_assistant_ref("a1", "x")
    )

    with pytest.raises(ValueError, match="x"):
        builder.publish(client, "p")


def test_publish_propagates_backend_rejection():
    workflows_api = _FakeWorkflowsApi(post_error=requests.HTTPError("400"))
    assistants_api = _FakeAssistantsApi([])
    client = _client_with(workflows_api, assistants_api)
    builder = _basic_builder()

    with pytest.raises(requests.HTTPError):
        builder.publish(client, "proj1")


def test_publish_inline_system_prompt_only_assistant():
    """Core happy path: publishing a definition whose only assistant is a
    purely inline, system_prompt-only assistant (no assistant_id, no name)
    must not be mistaken for an unresolved name reference and must not
    touch the assistants API at all."""
    workflows_api = _FakeWorkflowsApi()
    assistants_api = _FakeAssistantsApi([])
    client = _client_with(workflows_api, assistants_api)
    builder = (
        WorkflowBuilder("wf")
        .with_mode(WorkflowMode.SEQUENTIAL)
        .add_assistant("inline", system_prompt="You are a helpful planner.")
    )

    builder.publish(client, "proj1")

    _, json_data = workflows_api.post_calls[0]
    assert "system_prompt: You are a helpful planner." in json_data["yaml_config"]
    assert assistants_api.get_calls == 0


def test_publish_assistant_lookup_dedupes_and_sorts_by_name():
    """Regression: the default `update_date desc` sort has no tie-breaker, so
    offset paging over it can return the same row on two pages (or skip one).
    A sorted, de-duped lookup must not turn that into a false "ambiguous"
    error, and must ask for a stable sort explicitly."""
    workflows_api = _FakeWorkflowsApi()
    dup_across_pages = _assistant("x", "asst-1")
    assistants_api = _FakeAssistantsApi([dup_across_pages, dup_across_pages])
    client = _client_with(workflows_api, assistants_api)
    builder = (
        WorkflowBuilder("wf")
        .with_mode(WorkflowMode.SEQUENTIAL)
        .add_assistant_ref("a1", "x")
    )

    builder.publish(client, "p")

    _, json_data = workflows_api.post_calls[0]
    assert "assistant_id: asst-1" in json_data["yaml_config"]
    assert assistants_api.list_params[0]["sort_by"] == "name"
    assert assistants_api.list_params[0]["minimal_response"] is True


def test_publish_resolves_assistant_beyond_first_page():
    """Regression: name resolution must page past AssistantService's
    default per_page=12, not just read page 1."""
    workflows_api = _FakeWorkflowsApi()
    fillers = [_assistant(f"filler-{i}", f"asst-filler-{i}") for i in range(12)]
    target = _assistant("x", "asst-target")
    assistants_api = _FakeAssistantsApi(fillers + [target])
    client = _client_with(workflows_api, assistants_api)
    builder = (
        WorkflowBuilder("wf")
        .with_mode(WorkflowMode.SEQUENTIAL)
        .add_assistant_ref("a1", "x")
    )

    builder.publish(client, "p")

    _, json_data = workflows_api.post_calls[0]
    assert "assistant_id: asst-target" in json_data["yaml_config"]
    assert assistants_api.get_calls == 2
