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

"""Tests proving control-flow fields (condition/switch/iteration/retry/interrupt/
autonomous-mode) round-trip through ``WorkflowBuilder.add_state``/``with_mode``,
``.render()`` and ``WorkflowDefinition.to_yaml_config()``.

This task adds no new public builder/model surface: it only exercises the
existing `add_state(..., next=..., retry_policy=..., interrupt_before=...)`
and `with_mode(WorkflowMode.AUTONOMOUS)` parameters end to end.
"""

import pytest
import yaml
from pydantic import ValidationError

from codemie_sdk.models.workflow import WorkflowMode
from codemie_sdk.builders.workflow.builder import WorkflowBuilder
from codemie_sdk.builders.workflow.definition import (
    WorkflowNextState,
    WorkflowRetryPolicy,
    WorkflowStateCondition,
    WorkflowStateSwitch,
    WorkflowStateSwitchCondition,
)


def _find_state(states: list[dict], state_id: str) -> dict:
    for state in states:
        if state["id"] == state_id:
            return state
    raise AssertionError(f"state {state_id!r} not found in {states!r}")


def test_state_with_condition():
    builder = (
        WorkflowBuilder("wf")
        .add_assistant("a", system_prompt="do a", assistant_id="asst-1")
        .add_state(
            "s1",
            "a",
            "task",
            WorkflowNextState(
                condition=WorkflowStateCondition(
                    expression="x > 0", then="pos", otherwise="neg"
                )
            ),
        )
    )
    definition = builder.render()
    parsed = yaml.safe_load(definition.to_yaml_config())
    state = _find_state(parsed["states"], "s1")
    condition = state["next"]["condition"]
    assert condition == {"expression": "x > 0", "then": "pos", "otherwise": "neg"}


def test_state_with_switch():
    builder = (
        WorkflowBuilder("wf")
        .add_assistant("a", system_prompt="do a", assistant_id="asst-1")
        .add_state(
            "s1",
            "a",
            "task",
            WorkflowNextState(
                switch=WorkflowStateSwitch(
                    cases=[
                        WorkflowStateSwitchCondition(
                            condition="x == 1", state_id="one"
                        ),
                        WorkflowStateSwitchCondition(
                            condition="x == 2", state_id="two"
                        ),
                    ],
                    default="fallback",
                )
            ),
        )
    )
    definition = builder.render()
    parsed = yaml.safe_load(definition.to_yaml_config())
    state = _find_state(parsed["states"], "s1")
    switch = state["next"]["switch"]
    assert switch["default"] == "fallback"
    assert switch["cases"] == [
        {"condition": "x == 1", "state_id": "one"},
        {"condition": "x == 2", "state_id": "two"},
    ]


def test_iteration_iter_key_output_key():
    builder = (
        WorkflowBuilder("wf")
        .add_assistant("a", system_prompt="do a", assistant_id="asst-1")
        .add_state(
            "s1",
            "a",
            "task",
            WorkflowNextState(state_id="b", iter_key="items", output_key="result"),
        )
    )
    definition = builder.render()
    parsed = yaml.safe_load(definition.to_yaml_config())
    state = _find_state(parsed["states"], "s1")
    assert state["next"]["iter_key"] == "items"
    assert state["next"]["output_key"] == "result"


def test_retry_policy_all_four_fields():
    builder = (
        WorkflowBuilder("wf")
        .add_assistant("a", system_prompt="do a", assistant_id="asst-1")
        .add_state(
            "s1",
            "a",
            "task",
            WorkflowNextState(),
            retry_policy=WorkflowRetryPolicy(
                initial_interval=1.0,
                backoff_factor=2.0,
                max_interval=30.0,
                max_attempts=5,
            ),
        )
    )
    definition = builder.render()
    parsed = yaml.safe_load(definition.to_yaml_config())
    state = _find_state(parsed["states"], "s1")
    assert state["retry_policy"] == {
        "initial_interval": 1.0,
        "backoff_factor": 2.0,
        "max_interval": 30.0,
        "max_attempts": 5,
    }


def test_interrupt_before_flag():
    builder = (
        WorkflowBuilder("wf")
        .add_assistant("a", system_prompt="do a", assistant_id="asst-1")
        .add_state(
            "s1",
            "a",
            "task",
            WorkflowNextState(),
            interrupt_before=True,
        )
    )
    definition = builder.render()
    parsed = yaml.safe_load(definition.to_yaml_config())
    state = _find_state(parsed["states"], "s1")
    assert state["interrupt_before"] is True


def test_autonomous_mode_travels_with_definition():
    definition = WorkflowBuilder("wf").with_mode(WorkflowMode.AUTONOMOUS).render()
    assert definition.mode == WorkflowMode.AUTONOMOUS


def test_switch_requires_default():
    with pytest.raises(ValidationError):
        switch = WorkflowStateSwitch(
            cases=[WorkflowStateSwitchCondition(condition="x == 1", state_id="one")]
        )
        WorkflowBuilder("wf").add_assistant(
            "a", system_prompt="do a", assistant_id="asst-1"
        ).add_state("s1", "a", "task", WorkflowNextState(switch=switch))


@pytest.mark.parametrize(
    "missing_field",
    ["expression", "then", "otherwise"],
)
def test_condition_requires_all_three_fields(missing_field):
    fields = {"expression": "x > 0", "then": "pos", "otherwise": "neg"}
    del fields[missing_field]
    with pytest.raises(ValidationError):
        condition = WorkflowStateCondition(**fields)
        WorkflowBuilder("wf").add_assistant(
            "a", system_prompt="do a", assistant_id="asst-1"
        ).add_state("s1", "a", "task", WorkflowNextState(condition=condition))
