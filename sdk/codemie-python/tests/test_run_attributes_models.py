from unittest.mock import MagicMock, patch

import pytest

from codemie_sdk.models.assistant import AssistantChatRequest
from codemie_sdk.models.conversation import ConversationDetails
from codemie_sdk.models.workflow import WorkflowExecution
from codemie_sdk.services.workflow_execution import WorkflowExecutionService
from codemie_sdk.utils import ApiRequestHandler


def _ok_response(body: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = body
    return response


def test_chat_request_dumps_attributes_dict():
    request = AssistantChatRequest(text="hi", attributes={"team": "alpha"})

    dumped = request.model_dump(exclude_none=True, by_alias=True)

    assert dumped["attributes"] == {"team": "alpha"}

    omitted = AssistantChatRequest(text="hi").model_dump(
        exclude_none=True, by_alias=True
    )
    assert "attributes" not in omitted


def test_workflow_execution_create_sends_attributes_in_body():
    api = ApiRequestHandler("https://api.example.com", "token")
    service = WorkflowExecutionService(api, "wf1")

    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = _ok_response({})
        service.create(user_input="x", attributes={"team": "alpha"})

    assert post.call_args.kwargs["json"]["attributes"] == {"team": "alpha"}


def test_workflow_execution_create_without_attributes_sends_none():
    api = ApiRequestHandler("https://api.example.com", "token")
    service = WorkflowExecutionService(api, "wf1")

    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = _ok_response({})
        service.create(user_input="x")

    assert post.call_args.kwargs["json"].get("attributes") is None


def _conversation_details_payload() -> dict:
    return {
        "id": "c1",
        "date": "2026-01-01T00:00:00",
        "update_date": "2026-01-01T00:00:00",
        "conversation_id": "conv1",
        "conversation_name": "name",
        "llm_model": None,
        "folder": None,
        "pinned": False,
        "history": [],
        "user_id": "u1",
        "user_name": "user",
        "assistant_ids": [],
        "assistant_data": [],
        "initial_assistant_id": "a1",
        "final_user_mark": None,
        "final_operator_mark": None,
        "project": None,
        "conversation_details": None,
        "assistant_details": None,
        "user_abilities": None,
        "is_folder_migrated": True,
        "category": None,
    }


@pytest.mark.parametrize(
    "extra, expected",
    [
        ({"attributes": {"team": "alpha"}}, {"team": "alpha"}),
        ({"attributes": None}, None),
        ({}, None),
    ],
)
def test_conversation_details_parses_attributes_and_absent(extra, expected):
    details = ConversationDetails.model_validate(
        {**_conversation_details_payload(), **extra}
    )

    assert details.attributes == expected


@pytest.mark.parametrize(
    "extra, expected",
    [
        ({"attributes": {"team": "alpha"}}, {"team": "alpha"}),
        ({"attributes": None}, None),
        ({}, None),
    ],
)
def test_workflow_execution_response_parses_attributes_and_absent(extra, expected):
    execution = WorkflowExecution.model_validate(
        {
            "id": "e1",
            "execution_id": "e1",
            "workflow_id": "wf1",
            "overall_status": "Succeeded",
            "date": "2026-01-01T00:00:00",
            "prompt": "p",
            "update_date": None,
            "created_by": {"user_id": "u1", "username": "user", "name": "User"},
            **extra,
        }
    )

    assert execution.attributes == expected
