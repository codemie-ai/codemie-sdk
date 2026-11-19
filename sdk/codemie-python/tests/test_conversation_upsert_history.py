"""Tests for ConversationService.upsert_history() request headers."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from codemie_sdk.models.conversation import HistoryItem, UpsertHistoryRequest
from codemie_sdk.services.conversation import ConversationService

_CONVERSATION_ID = "conv-1"


def _service() -> ConversationService:
    return ConversationService("https://api.example.com", "test-token")


def _request() -> UpsertHistoryRequest:
    return UpsertHistoryRequest(
        history=[
            HistoryItem(
                role="User",
                message="hello",
                historyIndex=0,
                date=datetime(2026, 1, 1),
                fileNames=[],
            )
        ],
        folder="my-folder",
    )


def _raw_response() -> MagicMock:
    raw = MagicMock()
    raw.json.return_value = {
        "conversation_id": _CONVERSATION_ID,
        "new_messages": 1,
        "total_messages": 1,
        "created": True,
    }
    return raw


def _upsert(**kwargs):
    """Call upsert_history with requests.put patched; return the sent headers."""
    with patch(
        "codemie_sdk.utils.http.requests.put", return_value=_raw_response()
    ) as put:
        result = _service().upsert_history(_CONVERSATION_ID, _request(), **kwargs)
    assert result.conversation_id == _CONVERSATION_ID
    assert put.call_args.kwargs["url"].endswith(
        f"/v1/conversations/{_CONVERSATION_ID}/history"
    )
    return put.call_args.kwargs["headers"]


def test_upsert_history_sends_custom_headers():
    """Custom headers are added to the request next to the default ones."""
    headers = _upsert(headers={"X-CodeMie-Client": "codemie-gemini"})

    assert headers["X-CodeMie-Client"] == "codemie-gemini"
    assert headers["Authorization"] == "Bearer test-token"
    assert headers["Content-Type"] == "application/json"


def test_upsert_history_without_headers_sends_default_headers_only():
    """Omitting headers keeps the previous behaviour."""
    headers = _upsert()

    assert headers == {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-token",
    }
