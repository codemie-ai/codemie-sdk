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

"""Tests for the AI generation and refinement methods of the assistant and skill
services, using the DummyApi pattern of ``test_workflow_versions.py``.
"""

from types import SimpleNamespace

import pytest

from codemie_sdk.services.assistant import AssistantService
from codemie_sdk.services.skill import SkillService


class DummyApi:
    def __init__(self, response: dict):
        self.last_call = SimpleNamespace(
            endpoint=None, response_model=None, json_data=None, wrap_response=None
        )
        self._response = response

    def post(
        self, endpoint, response_model, json_data=None, wrap_response=True, **kwargs
    ):
        self.last_call.endpoint = endpoint
        self.last_call.response_model = response_model
        self.last_call.json_data = json_data
        self.last_call.wrap_response = wrap_response
        return self._response


@pytest.fixture
def assistant_service():
    service = AssistantService("https://api.example.com", "token")
    service._api = DummyApi({"name": "generated"})
    return service


@pytest.fixture
def skill_service():
    service = SkillService("https://api.example.com", "token")
    service._api = DummyApi({"name": "generated"})
    return service


def test_assistant_generate_posts_text_and_defaults(assistant_service):
    result = assistant_service.generate("An assistant that greets")

    call = assistant_service._api.last_call
    assert result == {"name": "generated"}
    assert call.endpoint == "/v1/assistants/generate"
    assert call.response_model is dict
    assert call.wrap_response is False
    assert call.json_data == {"text": "An assistant that greets", "include_tools": True}


def test_assistant_generate_sends_the_chosen_model(assistant_service):
    assistant_service.generate("text", include_tools=False, llm_model="model-x")

    assert assistant_service._api.last_call.json_data == {
        "text": "text",
        "include_tools": False,
        "llm_model": "model-x",
    }


def test_assistant_generate_prompt_omits_unset_fields(assistant_service):
    assistant_service.generate_prompt(system_prompt="Be brief")

    call = assistant_service._api.last_call
    assert call.endpoint == "/v1/assistants/prompt/generate"
    assert call.json_data == {"system_prompt": "Be brief"}


def test_assistant_refine_sends_draft_fields_and_flags(assistant_service):
    assistant_service.refine(
        name="Email",
        system_prompt="You help write emails",
        refine_prompt="Make it shorter",
        include_tools=False,
    )

    call = assistant_service._api.last_call
    assert call.endpoint == "/v1/assistants/refine"
    assert call.json_data == {
        "name": "Email",
        "system_prompt": "You help write emails",
        "refine_prompt": "Make it shorter",
        "include_tools": False,
        "include_context": True,
        "include_categories": True,
    }


def test_skill_generate_posts_text_and_defaults(skill_service):
    result = skill_service.generate("A skill that summarises notes")

    call = skill_service._api.last_call
    assert result == {"name": "generated"}
    assert call.endpoint == "/v1/skills/generate"
    assert call.response_model is dict
    assert call.wrap_response is False
    assert call.json_data == {
        "text": "A skill that summarises notes",
        "include_tools": True,
    }


def test_skill_refine_omits_unset_fields(skill_service):
    skill_service.refine(instructions="Summarise", refine_prompt="More detail")

    call = skill_service._api.last_call
    assert call.endpoint == "/v1/skills/refine"
    assert call.json_data == {
        "instructions": "Summarise",
        "refine_prompt": "More detail",
    }
