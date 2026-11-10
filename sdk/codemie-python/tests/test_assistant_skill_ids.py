import datetime

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
        return Assistant.model_validate(_assistant_payload(**self.assistant_extra))


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


def test_create_without_skills_omits_key():
    api = RecordingApi()
    _service(api).create(AssistantCreateRequest(**BASE))
    assert "skill_ids" not in api.bodies[0]


def test_create_sends_empty_skill_ids():
    api = RecordingApi()
    _service(api).create(AssistantCreateRequest(**BASE, skill_ids=[]))
    assert api.bodies[0]["skill_ids"] == []


def test_update_sends_empty_skill_ids():
    api = RecordingApi()
    _service(api).update("a1", AssistantUpdateRequest(**BASE, skill_ids=[]))
    assert api.bodies[0]["skill_ids"] == []


def test_update_without_skills_omits_key():
    api = RecordingApi()
    _service(api).update("a1", AssistantUpdateRequest(**BASE))
    assert "skill_ids" not in api.bodies[0]


def test_models_expose_skill_ids():
    assert Assistant.model_validate(_assistant_payload(skill_ids=["s1"])).skill_ids == [
        "s1"
    ]
    assert AssistantVersion.model_validate(
        _version_payload(skill_ids=["s2"])
    ).skill_ids == ["s2"]
    assert Assistant.model_validate(_assistant_payload()).skill_ids is None
    assert AssistantVersion.model_validate(_version_payload()).skill_ids is None


def test_rollback_fallback_uses_version_skill_ids():
    api = RecordingApi(
        version_extra={"skill_ids": ["v"]}, assistant_extra={"skill_ids": ["c"]}
    )
    _service(api).rollback_to_version("a1", 1)
    assert api.bodies[0]["skill_ids"] == ["v"]


def test_rollback_fallback_falls_back_to_current_skill_ids():
    api = RecordingApi(assistant_extra={"skill_ids": ["c"]})
    _service(api).rollback_to_version("a1", 1)
    assert api.bodies[0]["skill_ids"] == ["c"]


def test_rollback_fallback_empty_version_skill_ids_clears():
    api = RecordingApi(
        version_extra={"skill_ids": []}, assistant_extra={"skill_ids": ["c"]}
    )
    _service(api).rollback_to_version("a1", 1)
    assert api.bodies[0]["skill_ids"] == []
