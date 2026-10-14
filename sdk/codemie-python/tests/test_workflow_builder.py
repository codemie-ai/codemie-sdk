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

from codemie_sdk.builders.workflow.builder import WorkflowBuilder
from codemie_sdk.builders.workflow.definition import WorkflowNextState


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
