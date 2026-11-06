"""Workflow execution status wire contracts."""

import pytest
from pydantic import ValidationError

from codemie_sdk.models.workflow import ExecutionStatus, WorkflowExecution
from codemie_sdk.models.workflow_state import (
    WorkflowExecutionState,
    WorkflowExecutionStatusEnum,
)


STATUS_PAIRS = [
    ("IN_PROGRESS", "In Progress"),
    ("NOT_STARTED", "Not Started"),
    ("INTERRUPTED", "Interrupted"),
    ("FAILED", "Failed"),
    ("SUCCEEDED", "Succeeded"),
    ("ABORTED", "Aborted"),
    ("RECOVERING", "RECOVERING"),
    ("NEEDS_TRIAGE", "NEEDS_TRIAGE"),
    ("AUTHENTICATION_REQUIRED", "AUTHENTICATION_REQUIRED"),
]


def execution_payload():
    return {
        "id": "id-1",
        "execution_id": "execution-1",
        "workflow_id": "workflow-1",
        "date": "2026-11-06T10:00:00Z",
        "prompt": "test prompt",
        "update_date": "2026-11-06T10:01:00Z",
        "created_by": {"username": "user1", "name": "User One"},
    }


def state_payload():
    return {"id": "state-1", "execution_id": "execution-1", "name": "state"}


@pytest.mark.parametrize("member,wire_value", STATUS_PAIRS)
@pytest.mark.parametrize("status_field", ["overall_status", "status"])
def test_execution_parses_status_member(member, wire_value, status_field):
    execution = WorkflowExecution.model_validate(
        {**execution_payload(), status_field: wire_value}
    )
    assert execution.status is ExecutionStatus[member]
    assert execution.status.value == wire_value


@pytest.mark.parametrize("member,wire_value", STATUS_PAIRS)
def test_execution_state_parses_status_member(member, wire_value):
    state = WorkflowExecutionState.model_validate(
        {**state_payload(), "status": wire_value}
    )
    assert state.status is WorkflowExecutionStatusEnum[member]
    assert state.status.value == wire_value


def test_execution_rejects_unknown_status():
    with pytest.raises(ValidationError):
        WorkflowExecution.model_validate(
            {**execution_payload(), "overall_status": "FUTURE_STATUS"}
        )


def test_execution_state_rejects_unknown_status():
    with pytest.raises(ValidationError):
        WorkflowExecutionState.model_validate({**state_payload(), "status": "FUTURE_STATUS"})


def test_execution_state_defaults_to_not_started():
    state = WorkflowExecutionState.model_validate(state_payload())
    assert state.status is WorkflowExecutionStatusEnum.NOT_STARTED
