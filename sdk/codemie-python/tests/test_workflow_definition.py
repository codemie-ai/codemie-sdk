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

"""Unit tests for the mirrored builders.workflow definition models."""

import pytest
import yaml
from pydantic import ValidationError

from codemie_sdk.models.assistant import MCPServerConfig
from codemie_sdk.models.workflow import WorkflowMode
from codemie_sdk.builders.workflow.definition import (
    WorkflowAssistant,
    WorkflowAssistantTool,
    WorkflowDefinition,
    WorkflowMCPServer,
    WorkflowNextState,
    WorkflowRetryPolicy,
    WorkflowState,
    WorkflowStateCondition,
    WorkflowStateSwitch,
    WorkflowStateSwitchCondition,
    WorkflowTool,
)


class TestWorkflowAssistantTool:
    def test_construction(self):
        tool = WorkflowAssistantTool(name="jira_tool", integration_alias="jira-prod")
        assert tool.name == "jira_tool"
        assert tool.integration_alias == "jira-prod"

    def test_integration_alias_defaults_to_none(self):
        tool = WorkflowAssistantTool(name="jira_tool")
        assert tool.integration_alias is None

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            WorkflowAssistantTool(integration_alias="jira-prod")


class TestWorkflowAssistant:
    def test_construction(self):
        assistant = WorkflowAssistant(
            id="planner",
            assistant_id="asst-123",
            name="Planner",
            model="gpt-4o",
            temperature=0.7,
            system_prompt="You are a helpful planner.",
            tools=[WorkflowAssistantTool(name="jira_tool")],
            datasource_ids=["ds-1"],
            exclude_extra_context_tools=True,
            mcp_servers=[{"name": "svc", "enabled": False}],
            skill_ids=["skill-1"],
        )
        assert assistant.id == "planner"
        assert assistant.assistant_id == "asst-123"
        assert assistant.temperature == 0.7
        assert assistant.tools[0].name == "jira_tool"
        assert assistant.datasource_ids == ["ds-1"]
        assert assistant.exclude_extra_context_tools is True
        assert assistant.skill_ids == ["skill-1"]

    def test_defaults_when_optional_fields_omitted(self):
        assistant = WorkflowAssistant(system_prompt="You are a helpful planner.")
        assert assistant.id is None
        assert assistant.temperature is None
        assert assistant.limit_tool_output_tokens == 10000
        assert assistant.tools == []
        assert assistant.datasource_ids == []
        assert assistant.exclude_extra_context_tools is False
        assert assistant.mcp_servers == []
        assert assistant.skill_ids == []

    def test_temperature_above_range_raises(self):
        with pytest.raises(ValidationError):
            WorkflowAssistant(system_prompt="p", temperature=3.0)

    def test_temperature_below_range_raises(self):
        with pytest.raises(ValidationError):
            WorkflowAssistant(system_prompt="p", temperature=-0.1)

    def test_missing_all_identity_fields_raises(self):
        """No system_prompt/assistant_id/name: nothing to render or resolve."""
        with pytest.raises(ValidationError, match="system_prompt"):
            WorkflowAssistant()

    def test_inline_system_prompt_only_is_valid(self):
        """The documented core happy path: a purely inline assistant."""
        assistant = WorkflowAssistant(
            id="planner", system_prompt="You are a helpful planner."
        )
        assert assistant.assistant_id is None
        assert assistant.name is None
        assert assistant.system_prompt == "You are a helpful planner."

    def test_assistant_id_only_is_valid(self):
        assistant = WorkflowAssistant(id="planner", assistant_id="asst-123")
        assert assistant.system_prompt is None
        assert assistant.name is None

    def test_name_only_is_valid(self):
        assistant = WorkflowAssistant(id="ref", name="Planner")
        assert assistant.system_prompt is None
        assert assistant.assistant_id is None

    def test_enabled_mcp_server_missing_config_raises(self):
        with pytest.raises(ValidationError, match="missing"):
            WorkflowAssistant(
                system_prompt="p",
                mcp_servers=[WorkflowMCPServer(name="svc", enabled=True)],
            )

    def test_disabled_mcp_server_without_config_is_valid(self):
        assistant = WorkflowAssistant(
            system_prompt="p",
            mcp_servers=[WorkflowMCPServer(name="svc", enabled=False)],
        )
        assert assistant.mcp_servers[0].enabled is False

    def test_enabled_mcp_server_with_command_is_valid(self):
        assistant = WorkflowAssistant(
            system_prompt="p",
            mcp_servers=[WorkflowMCPServer(name="svc", enabled=True, command="npx")],
        )
        assert assistant.mcp_servers[0].command == "npx"

    def test_enabled_mcp_server_with_mcp_config_id_is_valid(self):
        assistant = WorkflowAssistant(
            system_prompt="p",
            mcp_servers=[
                WorkflowMCPServer(name="svc", enabled=True, mcp_config_id="cfg-1")
            ],
        )
        assert assistant.mcp_servers[0].mcp_config_id == "cfg-1"

    def test_enabled_mcp_server_with_config_dict_is_valid(self):
        """A plain dict is still accepted and coerced into MCPServerConfig."""
        assistant = WorkflowAssistant(
            system_prompt="p",
            mcp_servers=[
                WorkflowMCPServer(name="svc", enabled=True, config={"command": "npx"})
            ],
        )
        assert assistant.mcp_servers[0].config == MCPServerConfig(command="npx")

    def test_enabled_mcp_server_with_explicitly_empty_config_is_valid(self):
        """`config={}` (coerced to an all-default MCPServerConfig) still
        counts as "a config was provided" -- checked via `is not None`, not
        truthiness, since a model instance (unlike a dict) is always truthy
        regardless of its field contents.
        """
        assistant = WorkflowAssistant(
            system_prompt="p",
            mcp_servers=[WorkflowMCPServer(name="svc", enabled=True, config={})],
        )
        assert assistant.mcp_servers[0].config == MCPServerConfig()


class TestWorkflowStateCondition:
    def test_construction(self):
        condition = WorkflowStateCondition(
            expression="output == 'ok'",
            then="success_state",
            otherwise="failure_state",
        )
        assert condition.expression == "output == 'ok'"
        assert condition.then == "success_state"
        assert condition.otherwise == "failure_state"

    def test_missing_expression_raises(self):
        with pytest.raises(ValidationError):
            WorkflowStateCondition(then="a", otherwise="b")

    def test_missing_then_raises(self):
        with pytest.raises(ValidationError):
            WorkflowStateCondition(expression="x", otherwise="b")

    def test_missing_otherwise_raises(self):
        with pytest.raises(ValidationError):
            WorkflowStateCondition(expression="x", then="a")


class TestWorkflowStateSwitchCondition:
    def test_construction(self):
        case = WorkflowStateSwitchCondition(condition="x == 1", state_id="state_a")
        assert case.condition == "x == 1"
        assert case.state_id == "state_a"

    def test_missing_condition_raises(self):
        with pytest.raises(ValidationError):
            WorkflowStateSwitchCondition(state_id="state_a")

    def test_missing_state_id_raises(self):
        with pytest.raises(ValidationError):
            WorkflowStateSwitchCondition(condition="x == 1")


class TestWorkflowStateSwitch:
    def test_construction(self):
        switch = WorkflowStateSwitch(
            cases=[
                WorkflowStateSwitchCondition(condition="x == 1", state_id="state_a")
            ],
            default="state_default",
        )
        assert switch.default == "state_default"
        assert switch.cases[0].state_id == "state_a"

    def test_missing_cases_raises(self):
        with pytest.raises(ValidationError):
            WorkflowStateSwitch(default="state_default")

    def test_missing_default_raises(self):
        with pytest.raises(ValidationError):
            WorkflowStateSwitch(
                cases=[
                    WorkflowStateSwitchCondition(condition="x == 1", state_id="state_a")
                ]
            )


class TestWorkflowRetryPolicy:
    def test_construction(self):
        policy = WorkflowRetryPolicy(
            initial_interval=1.0,
            backoff_factor=2.0,
            max_interval=30.0,
            max_attempts=3,
        )
        assert policy.initial_interval == 1.0
        assert policy.backoff_factor == 2.0
        assert policy.max_interval == 30.0
        assert policy.max_attempts == 3

    def test_missing_initial_interval_raises(self):
        with pytest.raises(ValidationError):
            WorkflowRetryPolicy(backoff_factor=2.0, max_interval=30.0, max_attempts=3)

    def test_missing_backoff_factor_raises(self):
        with pytest.raises(ValidationError):
            WorkflowRetryPolicy(initial_interval=1.0, max_interval=30.0, max_attempts=3)

    def test_missing_max_interval_raises(self):
        with pytest.raises(ValidationError):
            WorkflowRetryPolicy(
                initial_interval=1.0, backoff_factor=2.0, max_attempts=3
            )

    def test_missing_max_attempts_raises(self):
        with pytest.raises(ValidationError):
            WorkflowRetryPolicy(
                initial_interval=1.0, backoff_factor=2.0, max_interval=30.0
            )


class TestWorkflowNextState:
    def test_construction_with_state_id(self):
        next_state = WorkflowNextState(state_id="next")
        assert next_state.state_id == "next"
        assert next_state.state_ids is None
        assert next_state.condition is None
        assert next_state.switch is None
        assert next_state.store_in_context is True
        assert next_state.include_in_llm_history is True
        assert next_state.clear_prior_messages is False
        assert next_state.clear_context_store is False
        assert next_state.reset_keys_in_context_store is None
        assert next_state.include_in_iterator_context == ["*"]
        assert next_state.append_to_context is False

    def test_construction_with_state_ids(self):
        next_state = WorkflowNextState(state_ids=["a", "b"])
        assert next_state.state_ids == ["a", "b"]
        assert next_state.state_id is None

    def test_construction_with_condition(self):
        next_state = WorkflowNextState(
            condition=WorkflowStateCondition(
                expression="output == 'ok'", then="a", otherwise="b"
            )
        )
        assert next_state.condition.then == "a"
        assert next_state.switch is None

    def test_construction_with_switch(self):
        next_state = WorkflowNextState(
            switch=WorkflowStateSwitch(
                cases=[WorkflowStateSwitchCondition(condition="x == 1", state_id="a")],
                default="b",
            )
        )
        assert next_state.switch.default == "b"
        assert next_state.condition is None

    def test_construction_with_no_target_is_allowed(self):
        next_state = WorkflowNextState()
        assert next_state.state_id is None
        assert next_state.state_ids is None

    def test_construction_with_bookkeeping_overrides(self):
        next_state = WorkflowNextState(
            state_id="next",
            iter_key="items",
            output_key="result",
            store_in_context=False,
            include_in_llm_history=False,
            clear_prior_messages=True,
            clear_context_store="keep_current",
            reset_keys_in_context_store=["temp"],
            include_in_iterator_context=["goal"],
            append_to_context=True,
        )
        assert next_state.iter_key == "items"
        assert next_state.output_key == "result"
        assert next_state.store_in_context is False
        assert next_state.include_in_llm_history is False
        assert next_state.clear_prior_messages is True
        assert next_state.clear_context_store == "keep_current"
        assert next_state.reset_keys_in_context_store == ["temp"]
        assert next_state.include_in_iterator_context == ["goal"]
        assert next_state.append_to_context is True

    def test_state_id_and_state_ids_raises(self):
        with pytest.raises(ValidationError):
            WorkflowNextState(state_id="a", state_ids=["b"])

    def test_state_id_and_condition_raises(self):
        with pytest.raises(ValidationError):
            WorkflowNextState(
                state_id="a",
                condition=WorkflowStateCondition(
                    expression="x", then="a", otherwise="b"
                ),
            )

    def test_condition_and_switch_raises(self):
        with pytest.raises(ValidationError):
            WorkflowNextState(
                condition=WorkflowStateCondition(
                    expression="x", then="a", otherwise="b"
                ),
                switch=WorkflowStateSwitch(
                    cases=[
                        WorkflowStateSwitchCondition(condition="x == 1", state_id="a")
                    ],
                    default="b",
                ),
            )

    def test_state_ids_and_switch_raises(self):
        with pytest.raises(ValidationError):
            WorkflowNextState(
                state_ids=["a"],
                switch=WorkflowStateSwitch(
                    cases=[
                        WorkflowStateSwitchCondition(condition="x == 1", state_id="a")
                    ],
                    default="b",
                ),
            )


class TestWorkflowState:
    def test_construction_with_assistant_id(self):
        state = WorkflowState(
            id="plan",
            assistant_id="asst-1",
            task="Plan the work",
            next=WorkflowNextState(state_id="code"),
        )
        assert state.id == "plan"
        assert state.assistant_id == "asst-1"
        assert state.task == "Plan the work"
        assert state.next.state_id == "code"
        assert state.retry_policy is None
        assert state.interrupt_before is False
        assert state.output_schema is None
        assert state.tool_args is None
        assert state.resolve_dynamic_values_in_prompt is False
        assert state.result_as_human_message is False
        assert state.finish_iteration is False

    def test_construction_with_tool_id(self):
        state = WorkflowState(
            id="run_tool", tool_id="tool-1", next=WorkflowNextState(state_id="s2")
        )
        assert state.tool_id == "tool-1"

    def test_construction_with_custom_node_id(self):
        state = WorkflowState(
            id="custom", custom_node_id="cn-1", next=WorkflowNextState(state_id="s2")
        )
        assert state.custom_node_id == "cn-1"

    def test_construction_with_workflow_id(self):
        state = WorkflowState(
            id="sub", workflow_id="wf-1", next=WorkflowNextState(state_id="s2")
        )
        assert state.workflow_id == "wf-1"

    def test_construction_with_retry_policy_and_interrupt(self):
        state = WorkflowState(
            id="code",
            assistant_id="asst-1",
            next=WorkflowNextState(state_id="s2"),
            retry_policy=WorkflowRetryPolicy(
                initial_interval=1.0,
                backoff_factor=2.0,
                max_interval=30.0,
                max_attempts=3,
            ),
            interrupt_before=True,
        )
        assert state.retry_policy.max_attempts == 3
        assert state.interrupt_before is True

    def test_missing_id_raises(self):
        with pytest.raises(ValidationError):
            WorkflowState(assistant_id="asst-1", next=WorkflowNextState(state_id="s2"))

    def test_missing_next_raises(self):
        with pytest.raises(ValidationError):
            WorkflowState(id="s", assistant_id="asst-1")

    def test_zero_type_refs_raises(self):
        with pytest.raises(ValidationError):
            WorkflowState(id="s", next=WorkflowNextState(state_id="s2"))

    def test_two_type_refs_raises(self):
        with pytest.raises(ValidationError):
            WorkflowState(
                id="s",
                assistant_id="asst-1",
                tool_id="tool-1",
                next=WorkflowNextState(state_id="s2"),
            )

    def test_three_type_refs_raises(self):
        with pytest.raises(ValidationError):
            WorkflowState(
                id="s",
                assistant_id="asst-1",
                tool_id="tool-1",
                custom_node_id="cn-1",
                next=WorkflowNextState(state_id="s2"),
            )


class TestWorkflowDefinitionRender:
    @staticmethod
    def _build_definition() -> WorkflowDefinition:
        assistants = {
            "planner": WorkflowAssistant(
                id="planner",
                assistant_id="asst-planner",
                name="Planner",
                system_prompt="Plan the work.",
            ),
            "coder": WorkflowAssistant(
                id="coder",
                assistant_id="asst-coder",
                name="Coder",
                system_prompt="Write the code.",
            ),
        }
        states = [
            WorkflowState(
                id="plan",
                assistant_id="asst-planner",
                task="Plan",
                next=WorkflowNextState(state_id="code"),
            ),
            WorkflowState(
                id="code",
                assistant_id="asst-coder",
                task="Code",
                next=WorkflowNextState(state_id="plan"),
                retry_policy=WorkflowRetryPolicy(
                    initial_interval=1.0,
                    backoff_factor=2.0,
                    max_interval=30.0,
                    max_attempts=3,
                ),
                interrupt_before=True,
            ),
        ]
        return WorkflowDefinition(
            name="demo",
            description="demo workflow",
            mode=WorkflowMode.SEQUENTIAL,
            shared=False,
            icon_url=None,
            assistants=assistants,
            states=states,
        )

    def test_byte_identical_repeat_renders(self):
        definition = self._build_definition()
        first = definition.to_yaml_config()
        second = definition.to_yaml_config()
        assert first == second
        assert isinstance(first, str)

    def test_round_trips_to_flat_assistants_and_states_lists(self):
        definition = self._build_definition()
        rendered = definition.to_yaml_config()
        payload = yaml.safe_load(rendered)

        assert list(payload.keys()) == ["assistants", "tools", "custom_nodes", "states"]
        assert isinstance(payload["assistants"], list)
        assert isinstance(payload["states"], list)
        assert payload["tools"] == []
        assert payload["custom_nodes"] == []

        assistant_ids = {a["assistant_id"] for a in payload["assistants"]}
        assert assistant_ids == {"asst-planner", "asst-coder"}

        state_by_id = {s["id"]: s for s in payload["states"]}
        assert set(state_by_id) == {"plan", "code"}
        assert state_by_id["plan"]["next"]["state_id"] == "code"
        assert "retry_policy" not in state_by_id["plan"]
        assert state_by_id["code"]["retry_policy"]["max_attempts"] == 3
        assert state_by_id["code"]["interrupt_before"] is True

    def test_unresolved_assistant_reference_raises_without_resolver(self):
        definition = WorkflowDefinition(
            name="demo",
            mode=WorkflowMode.SEQUENTIAL,
            assistants={"x": WorkflowAssistant(name="x")},
            states=[
                WorkflowState(
                    id="s",
                    assistant_id="asst-1",
                    next=WorkflowNextState(state_id="s"),
                )
            ],
        )
        with pytest.raises(ValueError, match="x"):
            definition.to_yaml_config()

    def test_unresolved_assistant_reference_resolved_with_resolver(self):
        definition = WorkflowDefinition(
            name="demo",
            mode=WorkflowMode.SEQUENTIAL,
            assistants={"x": WorkflowAssistant(name="x")},
            states=[
                WorkflowState(
                    id="s",
                    assistant_id="asst-1",
                    next=WorkflowNextState(state_id="s"),
                )
            ],
        )
        rendered = definition.to_yaml_config(
            resolve_assistant_name=lambda n: "resolved-id"
        )
        payload = yaml.safe_load(rendered)
        assert payload["assistants"][0]["assistant_id"] == "resolved-id"
        assert "resolved-id" in rendered

    def test_inline_assistant_with_name_and_system_prompt_is_not_a_reference(self):
        """Regression: a `name` on an inline assistant is for display, not
        resolution. With `system_prompt` set, this must render inline
        unresolved — never raise "unresolved reference", and never ask the
        resolver to substitute a different, same-named platform assistant."""
        definition = WorkflowDefinition(
            name="demo",
            mode=WorkflowMode.SEQUENTIAL,
            assistants={
                "a": WorkflowAssistant(id="a", system_prompt="p", name="Reviewer")
            },
            states=[
                WorkflowState(
                    id="s", assistant_id="a", next=WorkflowNextState(state_id="s")
                )
            ],
        )

        rendered = definition.to_yaml_config(
            resolve_assistant_name=lambda n: (_ for _ in ()).throw(
                AssertionError("resolver must not be called")
            )
        )
        payload = yaml.safe_load(rendered)
        assistant = payload["assistants"][0]
        assert assistant["system_prompt"] == "p"
        assert assistant["name"] == "Reviewer"
        assert "assistant_id" not in assistant

    def test_inline_system_prompt_only_assistant_renders_without_resolver(self):
        """Core happy path: a purely inline, system_prompt-only assistant (no
        assistant_id, no name) must render without ever being mistaken for an
        unresolved name reference, even with no `resolve_assistant_name`
        supplied."""
        definition = WorkflowDefinition(
            name="demo",
            mode=WorkflowMode.SEQUENTIAL,
            assistants={
                "inline": WorkflowAssistant(
                    id="inline", system_prompt="You are a helpful planner."
                )
            },
            states=[
                WorkflowState(
                    id="s",
                    assistant_id="inline",
                    next=WorkflowNextState(state_id="s"),
                )
            ],
        )
        rendered = definition.to_yaml_config()
        payload = yaml.safe_load(rendered)
        assert len(payload["assistants"]) == 1
        assistant = payload["assistants"][0]
        assert assistant["system_prompt"] == "You are a helpful planner."
        assert "assistant_id" not in assistant
        assert "name" not in assistant

    def test_assistant_without_id_defaults_to_dict_key(self):
        """A WorkflowAssistant built directly (not via the builder, which
        always sets `id`) has no `id` of its own; the dict key it lives under
        in `WorkflowDefinition.assistants` must still reach the backend."""
        definition = WorkflowDefinition(
            name="demo",
            mode=WorkflowMode.SEQUENTIAL,
            assistants={"planner": WorkflowAssistant(system_prompt="p")},
            states=[
                WorkflowState(
                    id="s",
                    assistant_id="planner",
                    next=WorkflowNextState(state_id="s"),
                )
            ],
        )
        payload = yaml.safe_load(definition.to_yaml_config())
        assert payload["assistants"][0]["id"] == "planner"


class TestMirroredModelsImmutability:
    def test_mutating_rendered_assistant_raises(self):
        assistant = WorkflowAssistant(id="a", system_prompt="p")
        with pytest.raises(ValidationError):
            assistant.system_prompt = "MUTATED"

    def test_mutating_rendered_state_raises(self):
        state = WorkflowState(
            id="s", assistant_id="a", task="t", next=WorkflowNextState(state_id="s")
        )
        with pytest.raises(ValidationError):
            state.task = "MUTATED"

    def test_mutation_does_not_leak_across_builder_branches(self):
        """Regression: WorkflowAssistant/WorkflowState/WorkflowNextState used
        to be the same shared instance across every builder branch and every
        `render()` result, so mutating one leaked into all of them."""
        from codemie_sdk.builders.workflow.builder import WorkflowBuilder

        base = WorkflowBuilder("wf").add_assistant("a", system_prompt="p")
        b1 = base.add_state("s", "a", "task", WorkflowNextState(state_id="end"))
        b2 = b1.with_description("x")

        rendered = b1.render()
        with pytest.raises(ValidationError):
            rendered.states[0].task = "MUTATED"
        with pytest.raises(ValidationError):
            rendered.assistants["a"].system_prompt = "MUTATED"

        assert b2.render().states[0].task == "task"
        assert base.render().assistants["a"].system_prompt == "p"

    def test_unknown_kwarg_on_assistant_raises(self):
        """Regression: a typo'd field (e.g. `modle` for `model`) used to be
        silently dropped by pydantic's default `extra="ignore"` instead of
        erroring, changing workflow behavior without any signal."""
        with pytest.raises(ValidationError):
            WorkflowAssistant(system_prompt="p", modle="gpt-4o")

    def test_unknown_kwarg_on_mcp_server_raises(self):
        with pytest.raises(ValidationError):
            WorkflowMCPServer(name="m", command="npx", arguments="-y pkg")

    def test_unknown_kwarg_on_next_state_raises(self):
        with pytest.raises(ValidationError):
            WorkflowNextState(state_id="end", keep_history=True)


class TestMcpServerConfigRendering:
    """The typed `MCPServerConfig` fills in defaults (`args`, `headers`, `env`,
    `single_usage`) and ignores unknown keys. Rendering must still print only
    what the caller wrote, or every existing workflow with an MCP server
    would change, and a typo'd key would vanish without a trace."""

    @staticmethod
    def _assistant_config(config):
        definition = WorkflowDefinition(
            name="wf",
            mode=WorkflowMode.SEQUENTIAL,
            assistants={
                "a": WorkflowAssistant(
                    system_prompt="p",
                    mcp_servers=[WorkflowMCPServer(name="s", config=config)],
                )
            },
        )
        rendered = yaml.safe_load(definition.to_yaml_config())
        return rendered["assistants"][0]["mcp_servers"][0]["config"]

    def test_only_the_keys_the_caller_set_are_rendered(self):
        assert self._assistant_config({"command": "uvx"}) == {"command": "uvx"}

    def test_omitted_args_are_not_rendered_as_an_empty_list(self):
        rendered = self._assistant_config({"command": "uvx", "env": {"A": "1"}})
        assert rendered == {"command": "uvx", "env": {"A": "1"}}

    def test_a_value_the_caller_set_explicitly_is_kept_even_if_it_is_a_default(self):
        rendered = self._assistant_config({"command": "uvx", "args": []})
        assert rendered == {"command": "uvx", "args": []}

    def test_an_mcp_server_config_instance_renders_only_its_set_fields(self):
        config = MCPServerConfig(command="npx", args=["-y", "pkg"])
        assert self._assistant_config(config) == {
            "command": "npx",
            "args": ["-y", "pkg"],
        }

    def test_an_empty_config_renders_as_empty(self):
        assert self._assistant_config({}) == {}

    def test_an_unknown_config_key_is_rejected(self):
        with pytest.raises(ValidationError, match="comand"):
            WorkflowMCPServer(name="s", config={"comand": "uvx"})

    def test_the_error_names_every_unknown_key(self):
        with pytest.raises(ValidationError) as error:
            WorkflowMCPServer(name="s", config={"comand": "x", "arg": []})
        assert "comand" in str(error.value)
        assert "arg" in str(error.value)

    def test_a_tool_nodes_mcp_server_config_renders_only_the_set_keys(self):
        definition = WorkflowDefinition(
            name="wf",
            mode=WorkflowMode.SEQUENTIAL,
            tools=[
                WorkflowTool(
                    id="run",
                    tool="run_command",
                    mcp_server=WorkflowMCPServer(
                        name="CLI", config={"command": "uvx", "args": ["cli"]}
                    ),
                )
            ],
        )
        server = yaml.safe_load(definition.to_yaml_config())["tools"][0]["mcp_server"]
        assert server["config"] == {"command": "uvx", "args": ["cli"]}

    def test_a_server_without_a_config_renders_no_config_key(self):
        definition = WorkflowDefinition(
            name="wf",
            mode=WorkflowMode.SEQUENTIAL,
            assistants={
                "a": WorkflowAssistant(
                    system_prompt="p",
                    mcp_servers=[
                        WorkflowMCPServer(name="s", mcp_config_id="catalog-1")
                    ],
                )
            },
        )
        server = yaml.safe_load(definition.to_yaml_config())["assistants"][0][
            "mcp_servers"
        ][0]
        assert "config" not in server
