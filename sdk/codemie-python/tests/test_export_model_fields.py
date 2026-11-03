import pytest
import yaml
from pydantic import ValidationError

from codemie_sdk.builders.workflow.definition import (
    WorkflowAssistantTool,
    WorkflowDefinition,
    WorkflowTool,
)
from codemie_sdk.models.assistant import (
    Assistant,
    AssistantCreateRequest,
    HedgingConfig,
    MCPServerConfig,
    ToolDetails,
    ToolKitDetails,
)
from codemie_sdk.models.workflow import (
    Workflow,
    WorkflowCreateRequest,
    WorkflowMode,
    WorkflowUpdateRequest,
)

ASSISTANT = {
    "name": "a",
    "description": "d",
    "system_prompt": "p",
    "project": "proj",
    "llm_model_type": "gpt",
}


def test_mcp_server_config_carries_audience_and_auth_config():
    config = MCPServerConfig(
        url="https://mcp", audience="aud", auth_config={"type": "oauth2"}
    )
    dumped = config.model_dump(exclude_none=True)
    assert dumped["audience"] == "aud"
    assert dumped["auth_config"] == {"type": "oauth2"}
    assert "oauth2" not in repr(config)


def test_assistant_request_carries_new_flags():
    request = AssistantCreateRequest(
        **ASSISTANT,
        interactive_enabled=True,
        enable_image_generation=True,
        file_attachment_enabled=False,
        hedging_config={"tool": {"name": "fast"}, "timeout_ms": 300},
    )
    body = request.model_dump(exclude_none=True)
    assert body["interactive_enabled"] is True
    assert body["enable_image_generation"] is True
    assert body["file_attachment_enabled"] is False
    assert body["hedging_config"]["tool"] == {"name": "fast"}
    assert body["hedging_config"]["timeout_ms"] == 300


def test_assistant_request_flags_are_unset_by_default():
    request = AssistantCreateRequest(**ASSISTANT)
    assert request.interactive_enabled is None
    assert request.enable_image_generation is None
    assert request.file_attachment_enabled is None
    assert request.hedging_config is None


def test_assistant_update_body_omits_unset_flags():
    from codemie_sdk.models.assistant import AssistantUpdateRequest

    body = AssistantUpdateRequest(**ASSISTANT).model_dump(exclude_none=True)
    assert "interactive_enabled" not in body
    assert "enable_image_generation" not in body
    assert "file_attachment_enabled" not in body


def test_assistant_read_exposes_new_flags():
    assistant = Assistant.model_validate(
        {
            **ASSISTANT,
            "interactive_enabled": True,
            "file_attachment_enabled": True,
            "hedging_config": {
                "provider_tool": {
                    "provider_name": "p",
                    "toolkit_name": "t",
                    "tool_name": "n",
                }
            },
        }
    )
    assert assistant.interactive_enabled is True
    assert assistant.file_attachment_enabled is True
    assert assistant.hedging_config.provider_tool.tool_name == "n"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {
            "tool": {"name": "x"},
            "provider_tool": {
                "provider_name": "p",
                "toolkit_name": "t",
                "tool_name": "n",
            },
        },
    ],
)
def test_hedging_requires_exactly_one_tool_source(payload):
    with pytest.raises(ValidationError, match="Exactly one"):
        HedgingConfig(**payload)


def test_tool_and_toolkit_auto_credentials_lookup_defaults_true_and_roundtrips():
    tool = ToolDetails(name="t")
    toolkit = ToolKitDetails(toolkit="k", tools=[tool])
    assert tool.auto_credentials_lookup is True
    assert toolkit.auto_credentials_lookup is True
    off = ToolKitDetails(
        toolkit="k",
        tools=[ToolDetails(name="t", auto_credentials_lookup=False)],
        auto_credentials_lookup=False,
    )
    dumped = off.model_dump()
    assert dumped["auto_credentials_lookup"] is False
    assert dumped["tools"][0]["auto_credentials_lookup"] is False


def test_workflow_models_carry_start_hint():
    assert (
        WorkflowCreateRequest(
            project="p", name="n", yaml_config="x: 1", start_hint="hi"
        ).start_hint
        == "hi"
    )
    assert (
        WorkflowUpdateRequest(
            project="p", name="n", description="d", yaml_config="x: 1", start_hint="hi"
        ).start_hint
        == "hi"
    )
    assert Workflow(project="p", name="n", start_hint="hi").start_hint == "hi"


def test_workflow_tool_carries_tool_access():
    tool = WorkflowTool(
        id="t1",
        tool="execute_workspace_script",
        tool_access=[WorkflowAssistantTool(name="jira", integration_alias="main")],
    )
    dumped = tool.model_dump(exclude_none=True)
    assert dumped["tool_access"] == [{"name": "jira", "integration_alias": "main"}]


def _definition(**extra):
    return WorkflowDefinition(name="w", mode=WorkflowMode.SEQUENTIAL, **extra)


def test_engine_switches_render_to_yaml_top_level():
    rendered = yaml.safe_load(
        _definition(
            enable_summarization_node=False,
            messages_limit_before_summarization=20,
            tokens_limit_before_summarization=5000,
            max_iteration_key_output_limit=100,
        ).to_yaml_config()
    )
    assert rendered["enable_summarization_node"] is False
    assert rendered["messages_limit_before_summarization"] == 20
    assert rendered["tokens_limit_before_summarization"] == 5000
    assert rendered["max_iteration_key_output_limit"] == 100


def test_unset_engine_switches_are_not_rendered():
    rendered = yaml.safe_load(_definition().to_yaml_config())
    assert "enable_summarization_node" not in rendered
    assert "messages_limit_before_summarization" not in rendered


@pytest.mark.parametrize(
    "name",
    [
        "messages_limit_before_summarization",
        "tokens_limit_before_summarization",
        "max_iteration_key_output_limit",
    ],
)
@pytest.mark.parametrize("value", [0, -5])
def test_engine_limits_reject_zero_and_negative(name, value):
    with pytest.raises(ValidationError, match=name):
        _definition(**{name: value})
