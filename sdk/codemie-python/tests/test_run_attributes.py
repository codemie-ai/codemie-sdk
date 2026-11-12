"""Tests for run attributes on chat, workflow execution and analytics requests."""

from unittest.mock import MagicMock, patch

from codemie_sdk.models.analytics import (
    PaginatedAnalyticsQueryParams,
    TabularResponse,
)
from codemie_sdk.models.assistant import AssistantChatRequest
from codemie_sdk.models.conversation import ConversationDetails
from codemie_sdk.models.workflow import WorkflowExecution
from codemie_sdk.services.analytics import AnalyticsService
from codemie_sdk.services.workflow_execution import WorkflowExecutionService

_TABULAR_BODY = {
    "data": {
        "columns": [{"id": "attributes", "label": "Attributes", "type": "json"}],
        "rows": [{"attributes": {"team": "alpha"}}],
    },
    "metadata": {
        "timestamp": "2026-01-01T00:00:00Z",
        "data_as_of": "2026-01-01T00:00:00Z",
        "filters_applied": {},
        "execution_time_ms": 1.0,
    },
}


def _ok_response(body: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = body
    return response


def test_chat_request_dumps_attributes_and_omits_them_when_unset():
    with_attributes = AssistantChatRequest(text="hi", attributes={"team": "alpha"})
    without_attributes = AssistantChatRequest(text="hi")

    assert with_attributes.model_dump(exclude_none=True)["attributes"] == {
        "team": "alpha"
    }
    assert "attributes" not in without_attributes.model_dump(exclude_none=True)


def test_workflow_execution_create_sends_attributes():
    api = MagicMock()
    service = WorkflowExecutionService(api, "wf-1")

    service.create(user_input="go", attributes={"team": "alpha"})

    payload = api.post.call_args.kwargs["json_data"]
    assert payload["attributes"] == {"team": "alpha"}


def test_workflow_execution_create_sends_null_attributes_by_default():
    api = MagicMock()
    service = WorkflowExecutionService(api, "wf-1")

    service.create(user_input="go")

    assert api.post.call_args.kwargs["json_data"]["attributes"] is None


def test_response_models_expose_attributes():
    execution = WorkflowExecution.model_validate(
        {
            "id": "1",
            "execution_id": "e1",
            "workflow_id": "w1",
            "overall_status": "Succeeded",
            "date": "2026-01-01T00:00:00Z",
            "prompt": "p",
            "update_date": None,
            "created_by": {"user_id": "u", "username": "n", "name": "n"},
            "attributes": {"team": "alpha"},
        }
    )

    assert execution.attributes == {"team": "alpha"}
    assert "attributes" in ConversationDetails.model_fields


def test_analytics_query_params_serialize_dict_attributes_to_json():
    params = PaginatedAnalyticsQueryParams(attributes={"team": "alpha", "env": "qa"})

    assert params.attributes == '{"team": "alpha", "env": "qa"}'
    assert PaginatedAnalyticsQueryParams(attributes='{"a": "b"}').attributes == (
        '{"a": "b"}'
    )
    assert "attributes" not in PaginatedAnalyticsQueryParams().model_dump(
        exclude_none=True
    )


def test_get_assistants_requests_sends_filters_and_parses_rows():
    service = AnalyticsService("https://api.example.com", "token")
    params = PaginatedAnalyticsQueryParams(attributes={"team": "alpha"})

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(_TABULAR_BODY)
        result = service.get_assistants_requests(params, assistant_id="asst-1")

    kwargs = get.call_args.kwargs
    assert kwargs["url"] == "https://api.example.com/v1/analytics/assistants-requests"
    assert kwargs["params"]["attributes"] == '{"team": "alpha"}'
    assert kwargs["params"]["assistant_id"] == "asst-1"
    assert isinstance(result, TabularResponse)
    assert result.data.rows == [{"attributes": {"team": "alpha"}}]


def test_get_workflows_executions_requests_endpoint():
    service = AnalyticsService("https://api.example.com", "token")

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(_TABULAR_BODY)
        result = service.get_workflows_executions(
            PaginatedAnalyticsQueryParams(attributes={"team": "alpha"})
        )

    kwargs = get.call_args.kwargs
    assert kwargs["url"] == "https://api.example.com/v1/analytics/workflows-executions"
    assert kwargs["params"]["attributes"] == '{"team": "alpha"}'
    assert result.data.rows == [{"attributes": {"team": "alpha"}}]


def test_get_attributes_usage_sends_attribute_key_only_when_given():
    service = AnalyticsService("https://api.example.com", "token")

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(_TABULAR_BODY)
        service.get_attributes_usage("team")
        with_key = get.call_args.kwargs
        service.get_attributes_usage()
        without_key = get.call_args.kwargs

    assert with_key["url"] == "https://api.example.com/v1/analytics/attributes-usage"
    assert with_key["params"]["attribute_key"] == "team"
    assert "attribute_key" not in without_key["params"]


def test_chat_request_sends_save_history_only_when_set():
    assert "save_history" not in AssistantChatRequest(text="hi").model_dump(
        exclude_none=True
    )
    assert (
        AssistantChatRequest(text="hi", save_history=False).model_dump(
            exclude_none=True
        )["save_history"]
        is False
    )
