from types import SimpleNamespace

from codemie_sdk.models.assistant import (
    Assistant,
    AssistantCreateRequest,
    AssistantUpdateRequest,
)
from codemie_sdk.models.llm import EffortLevel, LLMFeatures
from codemie_sdk.services.assistant import AssistantService

BASE = {
    "name": "a",
    "description": "d",
    "system_prompt": "p",
    "project": "proj",
    "llm_model_type": "claude",
}


class DummyApi:
    def __init__(self):
        self.last_call = SimpleNamespace(json_data=None)

    def put(self, endpoint, response_model, json_data=None, **kwargs):
        self.last_call.json_data = json_data
        return {"ok": True}


def _service(api):
    service = AssistantService("https://api.example.com", "token")
    service._api = api
    return service


def test_llm_features_effort_defaults_to_none():
    assert LLMFeatures().effort is None


def test_llm_features_parses_effort_levels():
    features = LLMFeatures.model_validate({"effort": ["low", "medium", "max"]})
    assert features.effort == [EffortLevel.LOW, EffortLevel.MEDIUM, EffortLevel.MAX]


def test_assistant_effort_defaults_to_none():
    assert Assistant.model_validate(BASE).effort is None


def test_assistant_parses_effort():
    assert Assistant.model_validate({**BASE, "effort": "max"}).effort == "max"


def test_create_request_serializes_effort():
    req = AssistantCreateRequest(**BASE, effort="high")
    assert req.model_dump(exclude_none=True)["effort"] == "high"


def test_update_service_sends_effort_when_set():
    api = DummyApi()
    _service(api).update("id1", AssistantUpdateRequest(**BASE, effort="low"))
    assert api.last_call.json_data["effort"] == "low"


def test_update_service_sends_explicit_null_when_effort_cleared():
    api = DummyApi()
    _service(api).update("id1", AssistantUpdateRequest(**BASE, effort=None))
    assert "effort" in api.last_call.json_data
    assert api.last_call.json_data["effort"] is None


def test_update_service_omits_effort_when_not_set():
    api = DummyApi()
    _service(api).update("id1", AssistantUpdateRequest(**BASE))
    assert "effort" not in api.last_call.json_data
