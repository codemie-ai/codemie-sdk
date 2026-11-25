from unittest.mock import MagicMock, patch

from codemie_sdk.models.conversation import ConversationMetrics
from codemie_sdk.services.assistant import AssistantService

_BASE = "https://api.example.com"


def _ok_response(body: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.content = b"{}"
    response.json.return_value = body
    return response


def _get_metrics(body: dict):
    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(body)
        result = AssistantService(_BASE, "token").get_conversation_metrics(
            "conversation-1"
        )
    return result, get.call_args.kwargs


def test_get_conversation_metrics_hits_url_and_parses_headroom_fields():
    result, kwargs = _get_metrics(
        {
            "conversation_id": "conversation-1",
            "total_input_tokens": 1200,
            "total_output_tokens": 80,
            "total_money_spent": 0.012,
            "money_spent_pending": False,
            "headroom_tokens_saved": 300,
            "headroom_tokens_original": 1500,
        }
    )

    assert kwargs["url"] == f"{_BASE}/v1/assistants/metrics/conversation-1"
    assert isinstance(result, ConversationMetrics)
    assert result.total_input_tokens == 1200
    assert result.headroom_tokens_saved == 300
    assert result.headroom_tokens_original == 1500


def test_get_conversation_metrics_without_savings_leaves_headroom_fields_none():
    result, _ = _get_metrics(
        {
            "conversation_id": "conversation-1",
            "total_input_tokens": 0,
            "total_output_tokens": 0,
        }
    )

    assert result.total_money_spent is None
    assert result.headroom_tokens_saved is None
    assert result.headroom_tokens_original is None


def test_get_conversation_metrics_reads_an_unwrapped_body():
    # The route returns the totals at the top level; a "data" key is not an envelope.
    result, _ = _get_metrics(
        {"conversation_id": "conversation-1", "data": {"conversation_id": "other"}}
    )

    assert result.conversation_id == "conversation-1"
