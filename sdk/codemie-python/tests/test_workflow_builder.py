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

"""Unit tests for the fluent, immutable WorkflowBuilder."""

import pytest
import yaml
from pydantic import ValidationError

from codemie_sdk.builders.workflow.builder import WorkflowBuilder
from codemie_sdk.builders.workflow.definition import (
    WorkflowEngineRetryPolicy,
    WorkflowNextState,
    WorkflowPoolConfig,
)


def test_add_assistant_requires_system_prompt_or_id():
    builder = WorkflowBuilder("wf")
    with pytest.raises(ValueError):
        builder.add_assistant("planner")


def test_add_assistant_ref_stays_unresolved():
    builder = WorkflowBuilder("wf").add_assistant_ref("planner", "the-name")
    definition = builder.render()
    assistant = definition.assistants["planner"]
    assert assistant.assistant_id is None
    assert assistant.name == "the-name"


def test_sequential_chaining_via_next():
    builder = (
        WorkflowBuilder("wf")
        .add_assistant("a", system_prompt="do a")
        .add_assistant("b", system_prompt="do b")
        .add_state("a", "a", "task a", WorkflowNextState(state_id="b"))
        .add_state("b", "b", "task b", WorkflowNextState())
    )
    definition = builder.render()
    assert definition.states[0].next.state_id == "b"


def test_immutability_independent_branches():
    base = WorkflowBuilder("wf").add_assistant("a", system_prompt="do a")

    b1 = base.add_state("s1", "a", "task one", WorkflowNextState())
    b2 = base.add_state("s2", "a", "task two", WorkflowNextState())

    assert base.render().states == []
    assert b1.render().states != b2.render().states


def test_deterministic_render():
    def _build():
        return (
            WorkflowBuilder("wf")
            .add_assistant("a", assistant_id="asst-1", name="A")
            .add_state("s1", "a", "task", WorkflowNextState())
            .render()
            .to_yaml_config()
        )

    assert _build() == _build()


def test_workflow_mode_exported_from_package():
    """Regression: `with_mode()` needs `WorkflowMode`, but the package only
    re-exported the builder/definition classes, not the enum itself."""
    from codemie_sdk.builders.workflow import WorkflowMode as ReExportedMode
    from codemie_sdk.models.workflow import WorkflowMode

    assert ReExportedMode is WorkflowMode


def test_add_state_unknown_assistant_raises():
    builder = WorkflowBuilder("wf")
    with pytest.raises(ValueError, match="missing"):
        builder.add_state("s1", "missing", "task", WorkflowNextState())


def test_builder_requires_name():
    with pytest.raises(ValueError, match="name"):
        WorkflowBuilder(None)


def test_builder_rejects_empty_name():
    with pytest.raises(ValueError, match="name"):
        WorkflowBuilder("")


def test_duplicate_assistant_id_raises():
    builder = WorkflowBuilder("wf").add_assistant("a", system_prompt="do a")
    with pytest.raises(ValueError, match="a"):
        builder.add_assistant("a", system_prompt="do a again")


def test_duplicate_state_id_raises():
    builder = (
        WorkflowBuilder("wf")
        .add_assistant("a", system_prompt="do a")
        .add_state("s1", "a", "task one", WorkflowNextState())
    )
    with pytest.raises(ValueError, match="s1"):
        builder.add_state("s1", "a", "task two", WorkflowNextState())


def test_engine_setters_are_immutable_and_render():
    base = WorkflowBuilder("wf")
    full = (
        base.with_max_concurrency(10)
        .with_recursion_limit(50)
        .with_verbose(True)
        .with_type("custom")
        .with_max_nesting_level(2)
        .with_pool_config(WorkflowPoolConfig(enabled=True))
        .with_retry_policy(WorkflowEngineRetryPolicy(max_attempts=2))
        .with_summarization_node(True)
        .with_summarization_limits(messages=5)
        .with_summarization_limits(tokens=500)
        .with_max_iteration_key_output_limit(7)
    )
    assert "max_concurrency" not in yaml.safe_load(base.render().to_yaml_config())
    rendered = yaml.safe_load(full.render().to_yaml_config())
    assert rendered["max_concurrency"] == 10
    assert rendered["recursion_limit"] == 50
    assert rendered["verbose"] is True
    assert rendered["type"] == "custom"
    assert rendered["max_nesting_level"] == 2
    assert rendered["pool_config"] == {"enabled": True}
    assert rendered["retry_policy"] == {"max_attempts": 2}
    assert rendered["enable_summarization_node"] is True
    assert rendered["messages_limit_before_summarization"] == 5
    assert rendered["tokens_limit_before_summarization"] == 500
    assert rendered["max_iteration_key_output_limit"] == 7


def test_summarization_limits_none_not_set():
    rendered = yaml.safe_load(
        WorkflowBuilder("wf").with_summarization_limits().render().to_yaml_config()
    )
    assert "messages_limit_before_summarization" not in rendered


def test_invalid_engine_value_fails_at_render():
    builder = WorkflowBuilder("wf").with_max_concurrency(0)
    with pytest.raises(ValidationError, match="max_concurrency"):
        builder.render()
