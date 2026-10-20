import datetime
from types import SimpleNamespace

import pytest
import requests

from codemie_sdk.models.assistant import (
    Assistant,
    AssistantCreateRequest,
    AssistantUpdateRequest,
    AssistantVersion,
    ToolKitDetails,
)
from codemie_sdk.services.assistant import AssistantService


class RecordingApi:
    def __init__(self):
        self.calls = []
        self.error = None
        self.get_responses = {}

    def post(self, endpoint, response_model, json_data=None, **kwargs):
        self.calls.append(("post", endpoint, json_data))
        if self.error:
            raise self.error
        return {"assistant_id": "a1"} if endpoint == "/v1/assistants" else {}

    def put(self, endpoint, response_model, json_data=None, **kwargs):
        self.calls.append(("put", endpoint, json_data))
        if self.error:
            raise self.error
        return {}

    def get(self, endpoint, response_model, params=None, wrap_response=True):
        self.calls.append(("get", endpoint, None))
        return self.get_responses[endpoint]


def make_service():
    service = AssistantService("https://api.example.com", "token")
    api = RecordingApi()
    service._api = api
    return service, api


BASE = dict(
    name="n",
    description="d",
    system_prompt="p",
    project="proj",
    llm_model_type="gpt-4o",
)


def create_req(**extra):
    return AssistantCreateRequest(**BASE, **extra)


def update_req(**extra):
    return AssistantUpdateRequest(**BASE, **extra)


def payload(api):
    return api.calls[-1][2]


def test_create_sends_field_when_set():
    service, api = make_service()
    service.create(create_req(deselected_default_tools=["search_kb"]))
    assert payload(api)["deselected_default_tools"] == ["search_kb"]


def test_update_sends_changed_list():
    service, api = make_service()
    service.update("a1", update_req(deselected_default_tools=["search_code_repo"]))
    assert payload(api)["deselected_default_tools"] == ["search_code_repo"]


def test_unset_field_omitted_from_payload():
    service, api = make_service()
    service.create(create_req())
    assert "deselected_default_tools" not in payload(api)
    service.update("a1", update_req())
    assert "deselected_default_tools" not in payload(api)


def test_explicit_empty_list_is_sent():
    service, api = make_service()
    service.create(create_req(deselected_default_tools=[]))
    assert payload(api)["deselected_default_tools"] == []
    service.update("a1", update_req(deselected_default_tools=[]))
    assert payload(api)["deselected_default_tools"] == []


def _version(**extra):
    return {
        "version_number": 1,
        "created_date": datetime.datetime.now(datetime.UTC).isoformat(),
        "system_prompt": "p",
        **extra,
    }


def test_read_models_expose_field_and_default_empty():
    assistant = dict(BASE)
    assert Assistant(**assistant).deselected_default_tools == []
    assert Assistant(
        **assistant, deselected_default_tools=["search_kb"]
    ).deselected_default_tools == ["search_kb"]
    assert AssistantVersion(**_version()).deselected_default_tools == []
    assert AssistantVersion(
        **_version(deselected_default_tools=["search_kb"])
    ).deselected_default_tools == ["search_kb"]


def test_backend_rejection_propagates():
    service, api = make_service()
    api.error = requests.HTTPError("400 bad tool name")
    with pytest.raises(requests.HTTPError):
        service.create(create_req(deselected_default_tools=["nope"]))


def test_get_tools_returns_default_datasource_toolkit_unchanged():
    service, api = make_service()
    names = ["search_kb", "search_code_repo", "get_repository_file_tree"]
    api.get_responses["/v1/assistants/tools"] = [
        ToolKitDetails(toolkit="Datasource", tools=[{"name": n} for n in names])
    ]
    result = service.get_tools()
    assert [t.name for t in result[0].tools] == names


def test_rollback_fallback_carries_field():
    service, api = make_service()
    rollback_error = requests.HTTPError("rollback failed")

    def post(endpoint, response_model, json_data=None, **kwargs):
        api.calls.append(("post", endpoint, json_data))
        if endpoint.endswith("/rollback"):
            raise rollback_error
        return {}

    api.post = post
    # Assistant has no `user_prompts` attribute, which the fallback reads
    # (pre-existing); use a stand-in exposing it so the fallback is reachable.
    api.get_responses["/v1/assistants/id/a1"] = SimpleNamespace(
        **Assistant(**BASE, deselected_default_tools=["search_kb"]).model_dump(),
        user_prompts=[],
    )
    api.put = lambda endpoint, response_model, json_data=None, **kw: (
        api.calls.append(("put", endpoint, json_data)) or response_model(message="ok")
    )
    api.get_responses["/v1/assistants/a1/versions/2"] = AssistantVersion(
        **_version(deselected_default_tools=["search_code_repo"])
    )
    service.rollback_to_version("a1", 2)
    put = [c for c in api.calls if c[0] == "put"][-1]
    assert put[2]["deselected_default_tools"] == ["search_code_repo"]
