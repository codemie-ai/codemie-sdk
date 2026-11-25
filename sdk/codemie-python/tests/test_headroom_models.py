from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from codemie_sdk.models.assistant import (
    Assistant,
    AssistantCreateRequest,
    AssistantUpdateRequest,
)
from codemie_sdk.models.common import TokensUsage
from codemie_sdk.models.conversation import HistoryItem
from codemie_sdk.models.headroom import (
    HeadroomConfig,
    HeadroomOverride,
    HeadroomSavings,
    HeadroomStrategy,
)
from codemie_sdk.models.workflow import Workflow
from codemie_sdk.services.assistant import AssistantService

BASE = {
    "name": "a",
    "description": "d",
    "system_prompt": "p",
    "project": "proj",
    "llm_model_type": "gpt",
}

DEFAULT_CONFIG = {
    "enabled": True,
    "compress_user_messages": True,
    "compress_tool_outputs": True,
    "strategy": "balanced",
}


class DummyApi:
    def __init__(self):
        self.last_call = SimpleNamespace(json_data=None)

    def post(self, endpoint, response_model, json_data=None, **kwargs):
        self.last_call.json_data = json_data
        return {"ok": True}

    def put(self, endpoint, response_model, json_data=None, **kwargs):
        self.last_call.json_data = json_data
        return {"ok": True}


def _service(api):
    service = AssistantService("https://api.example.com", "token")
    service._api = api
    return service


def test_create_sends_headroom_config_with_defaults_filled():
    api = DummyApi()
    _service(api).create(
        AssistantCreateRequest(**BASE, headroom_config={"enabled": True})
    )
    assert api.last_call.json_data["headroom_config"] == DEFAULT_CONFIG


def test_update_sends_headroom_config_with_defaults_filled():
    api = DummyApi()
    _service(api).update(
        "id1", AssistantUpdateRequest(**BASE, headroom_config={"enabled": True})
    )
    assert api.last_call.json_data["headroom_config"] == DEFAULT_CONFIG


def test_create_omits_headroom_config_when_not_set():
    api = DummyApi()
    _service(api).create(AssistantCreateRequest(**BASE))
    assert "headroom_config" not in api.last_call.json_data


def test_update_omits_headroom_config_when_not_set():
    api = DummyApi()
    _service(api).update("id1", AssistantUpdateRequest(**BASE))
    assert "headroom_config" not in api.last_call.json_data


def test_config_defaults():
    config = HeadroomConfig()
    assert config.enabled is False
    assert config.compress_user_messages is True
    assert config.compress_tool_outputs is True
    assert config.strategy == HeadroomStrategy.BALANCED


def test_config_rejects_invalid_strategy():
    with pytest.raises(ValidationError):
        HeadroomConfig(strategy="bogus")


def test_assistant_parses_headroom_config():
    assistant = Assistant.model_validate(
        {**BASE, "headroom_config": {"enabled": True, "strategy": "lossless"}}
    )
    assert assistant.headroom_config.enabled is True
    assert assistant.headroom_config.strategy == "lossless"


def test_assistant_headroom_config_defaults_to_none():
    assert Assistant.model_validate(BASE).headroom_config is None


def test_workflow_parses_partial_headroom_override():
    workflow = Workflow.model_validate(
        {"project": "p", "name": "w", "headroom_config": {"strategy": "aggressive"}}
    )
    override = workflow.headroom_config
    assert isinstance(override, HeadroomOverride)
    assert override.strategy == "aggressive"
    assert override.enabled is None
    assert override.compress_user_messages is None
    assert override.compress_tool_outputs is None


def test_history_item_parses_headroom_savings_open_values():
    item = HistoryItem.model_validate(
        {
            "role": "Assistant",
            "message": "m",
            "historyIndex": 0,
            "date": "2026-01-01T00:00:00",
            "fileNames": [],
            "headroom": {
                "tokens_original": 100,
                "tokens_compacted": 60,
                "tokens_saved": 40,
                "mode": "mixed",
                "strategy": None,
                "unknown_key": "ignored",
            },
        }
    )
    savings = item.headroom
    assert isinstance(savings, HeadroomSavings)
    assert savings.mode == "mixed"
    assert savings.strategy is None
    assert savings.calls == 1
    assert savings.tokens_saved == 40
    assert not hasattr(savings, "unknown_key")


def test_tokens_usage_parses_headroom_savings():
    usage = TokensUsage.model_validate(
        {
            "input_tokens": 1,
            "headroom": {
                "tokens_original": 10,
                "tokens_compacted": 5,
                "tokens_saved": 5,
                "mode": "tool_outputs",
                "strategy": "custom-strategy",
                "calls": 3,
            },
        }
    )
    assert usage.headroom.strategy == "custom-strategy"
    assert usage.headroom.calls == 3


def test_headroom_defaults_to_none_on_history_and_usage():
    assert TokensUsage().headroom is None
    item = HistoryItem.model_validate(
        {
            "role": "User",
            "message": "m",
            "historyIndex": 0,
            "date": "2026-01-01T00:00:00",
            "fileNames": [],
        }
    )
    assert item.headroom is None
