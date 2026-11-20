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

"""Unit tests for the LLMModel fields returned by the models list endpoint."""

from codemie_sdk.models.llm import LLMModel


def test_parses_direct_model_payload():
    model = LLMModel.model_validate(
        {
            "base_name": "claude-haiku-4-5-20251001-dial",
            "cost": {"input": 0.000001, "output": 0.000005},
            "default": False,
            "default_for_categories": [],
            "deployment_name": "claude-haiku-4-5-20251001-dial",
            "enabled": True,
            "forbidden_for_web": False,
            "is_premium": False,
            "label": "Claude Haiku 4.5 20251001 (DIAL)",
            "max_input_tokens": 200000,
            "max_output_tokens": 64000,
            "multimodal": True,
            "provider": "anthropic",
            "react_agent": False,
            "status": "enabled",
            "supports_image_generation": False,
            "switchyard": [],
        }
    )

    assert model.max_input_tokens == 200000
    assert model.default_for_categories == []
    assert model.forbidden_for_web is False
    assert model.supports_image_generation is False
    assert model.switchyard == []


def test_parses_switchyard_router_payload():
    model = LLMModel.model_validate(
        {
            "base_name": "sy-signal-gpt",
            "default": False,
            "default_for_categories": [],
            "enabled": True,
            "forbidden_for_web": True,
            "is_premium": False,
            "is_router": True,
            "label": "SY Signal GPT",
            "max_input_tokens": 922000,
            "multimodal": True,
            "provider": "azure_openai",
            "router_type": "switchyard",
            "status": "enabled",
            "strategy": "signal",
            "supports_tools": True,
            "tiers": {"simple": {"model": "gpt-6-luna", "label": "GPT-6 Luna"}},
        }
    )

    assert model.is_router is True
    assert model.router_type == "switchyard"
    assert model.strategy == "signal"
    assert model.tiers["simple"].model == "gpt-6-luna"
    assert model.tiers["simple"].label == "GPT-6 Luna"


def test_parses_classifier_router_payload():
    model = LLMModel.model_validate(
        {
            "base_name": "claude-router-standard",
            "classifier_model": "claude-haiku-5-5",
            "enabled": True,
            "is_router": True,
            "max_input_tokens": 1000000,
            "provider": "aws_bedrock",
            "router_type": "litellm_auto",
            "strategy": "classifier",
            "tiers": {
                "simple": {
                    "model": "claude-haiku-5-5",
                    "label": "Bedrock Claude Haiku 5.5",
                }
            },
        }
    )

    assert model.classifier_model == "claude-haiku-5-5"
    assert model.tiers["simple"].label == "Bedrock Claude Haiku 5.5"


def test_parses_switchyard_routes_on_model():
    model = LLMModel.model_validate(
        {
            "base_name": "gpt-6-sol",
            "enabled": True,
            "provider": "azure_openai",
            "switchyard": [
                {
                    "base_name": "sy-signal-gpt",
                    "label": "SY Signal GPT",
                    "efficient": "gpt-6-luna",
                    "mode": "signal",
                }
            ],
        }
    )

    assert model.switchyard[0].base_name == "sy-signal-gpt"
    assert model.switchyard[0].efficient == "gpt-6-luna"


def test_new_fields_default_to_none_when_absent():
    model = LLMModel(base_name="m", enabled=True)

    assert model.max_input_tokens is None
    assert model.tiers is None
    assert model.switchyard is None
    assert model.supports_image_generation is None
