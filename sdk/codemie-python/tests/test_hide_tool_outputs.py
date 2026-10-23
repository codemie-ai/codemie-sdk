from types import SimpleNamespace

from codemie_sdk.models.assistant import (
    Assistant,
    AssistantCreateRequest,
    AssistantUpdateRequest,
)
from codemie_sdk.models.conversation import AssistantDataItem, AssistantDetailsData
from codemie_sdk.services.assistant import AssistantService

BASE = {
    "name": "a",
    "description": "d",
    "system_prompt": "p",
    "project": "proj",
    "llm_model_type": "gpt",
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


def test_assistant_defaults_to_false_when_missing():
    assert Assistant.model_validate(BASE).hide_tool_outputs is False


def test_assistant_parses_true():
    assert (
        Assistant.model_validate({**BASE, "hide_tool_outputs": True}).hide_tool_outputs
        is True
    )


def test_create_request_serializes_flag():
    req = AssistantCreateRequest(**BASE, hide_tool_outputs=True)
    assert req.model_dump()["hide_tool_outputs"] is True


def test_update_request_omits_flag_when_not_set():
    req = AssistantUpdateRequest(**BASE)
    assert "hide_tool_outputs" not in req.model_dump(exclude_unset=True)


def test_update_service_omits_flag_when_not_set():
    api = DummyApi()
    service = _service(api)
    service.update("id1", AssistantUpdateRequest(**BASE))
    assert "hide_tool_outputs" not in api.last_call.json_data


def test_update_service_sends_flag_when_set():
    api = DummyApi()
    service = _service(api)
    service.update("id1", AssistantUpdateRequest(**BASE, hide_tool_outputs=False))
    assert api.last_call.json_data["hide_tool_outputs"] is False


def test_conversation_assistant_details_default_false():
    data = AssistantDetailsData(
        assistant_id="1",
        assistant_name="n",
        assistant_icon=None,
        assistant_type=None,
        context=[],
        tools=[],
        conversation_starters=[],
    )
    assert data.hide_tool_outputs is False


def _data_item(**extra):
    return AssistantDataItem(
        assistant_id="1",
        assistant_name="n",
        assistant_icon=None,
        assistant_type=None,
        **extra,
    )


def test_conversation_assistant_data_item_default_false():
    assert _data_item().hide_tool_outputs is False


def test_conversation_assistant_data_item_keeps_true():
    assert _data_item(hide_tool_outputs=True).hide_tool_outputs is True
