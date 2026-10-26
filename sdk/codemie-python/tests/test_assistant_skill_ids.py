import datetime
from types import SimpleNamespace

import pytest
import requests

from codemie_sdk.models.assistant import (
    Assistant,
    AssistantCreateRequest,
    AssistantUpdateRequest,
    AssistantVersion,
)
from codemie_sdk.services.assistant import AssistantService

BASE = {
    "name": "a",
    "description": "d",
    "system_prompt": "p",
    "project": "proj",
    "llm_model_type": "gpt",
}
NOW = datetime.datetime.now(datetime.UTC).isoformat()


def _assistant_payload(**extra):
    return {
        "id": "a1",
        "name": "a",
        "description": "d",
        "system_prompt": "cur",
        "project": "proj",
        "llm_model_type": "gpt",
        "created_date": NOW,
        **extra,
    }


def _version_payload(**extra):
    return {
        "version_number": 1,
        "created_date": NOW,
        "system_prompt": "v1",
        **extra,
    }


class AssistantWithPrompts(Assistant):
    # the rollback fallback reads user_prompts, which the read model ignores
    user_prompts: list[str] = []


class RecordingApi:
    def __init__(self, version_extra=None, assistant_extra=None):
        self.bodies = []
        self.version_extra = version_extra or {}
        self.assistant_extra = assistant_extra or {}

    def post(self, endpoint, response_model, json_data=None, **kwargs):
        if endpoint.endswith("/rollback"):
            raise requests.HTTPError("boom")
        self.bodies.append(json_data)
        return response_model.model_validate({"message": "ok", "assistant_id": "a1"})

    def put(self, endpoint, response_model, json_data=None, **kwargs):
        self.bodies.append(json_data)
        return response_model.model_validate({"message": "ok"})

    def get(self, endpoint, response_model, params=None, wrap_response=True):
        if "/versions/" in endpoint:
            return AssistantVersion.model_validate(
                _version_payload(**self.version_extra)
            )
        return AssistantWithPrompts.model_validate(
            _assistant_payload(**self.assistant_extra)
        )


def _service(api):
    service = AssistantService("https://api.example.com", "token")
    service._api = api
    return service


def test_create_sends_skill_ids():
    api = RecordingApi()
    _service(api).create(AssistantCreateRequest(**BASE, skill_ids=["s1"]))
    assert api.bodies[0]["skill_ids"] == ["s1"]


def test_update_sends_skill_ids():
    api = RecordingApi()
    _service(api).update("a1", AssistantUpdateRequest(**BASE, skill_ids=["s1"]))
    assert api.bodies[0]["skill_ids"] == ["s1"]


def test_update_without_skills_omits_key():
    api = RecordingApi()
    _service(api).update("a1", AssistantUpdateRequest(**BASE))
    assert "skill_ids" not in api.bodies[0]


def test_models_expose_skill_ids():
    assert Assistant.model_validate(_assistant_payload(skill_ids=["s1"])).skill_ids == ["s1"]
    assert AssistantVersion.model_validate(_version_payload(skill_ids=["s2"])).skill_ids == ["s2"]
    assert Assistant.model_validate(_assistant_payload()).skill_ids is None
    assert AssistantVersion.model_validate(_version_payload()).skill_ids is None

