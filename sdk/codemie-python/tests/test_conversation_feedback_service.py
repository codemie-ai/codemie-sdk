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


"""Unit tests for the feedback list and get methods of ConversationService."""

from unittest.mock import MagicMock, patch

from codemie_sdk.models.conversation import FeedbackEntry, FeedbackMark
from codemie_sdk.services.conversation import ConversationService

_ENTRY = {
    "id": "feedback-1",
    "request": "What is 2 + 2?",
    "response": "4",
    "comments": "Not helpful",
    "date": "2026-01-01T10:00:00",
    "update_date": "2026-01-01T10:05:00",
    "conversationId": "conversation-1",
    "history": [],
    "mark": "wrong",
    "appName": None,
    "repoName": None,
    "indexType": None,
}


def _ok_response(body) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.content = b"{}"
    response.json.return_value = body
    return response


def _service() -> ConversationService:
    return ConversationService("https://api.example.com", "token")


def test_list_feedback_requests_collection_and_parses_entries():
    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response([_ENTRY])
        result = _service().list_feedback()

    assert get.call_args.kwargs["url"] == "https://api.example.com/v1/feedback"
    assert len(result) == 1
    assert isinstance(result[0], FeedbackEntry)
    assert result[0].id == "feedback-1"
    assert result[0].conversation_id == "conversation-1"
    assert result[0].mark == FeedbackMark.WRONG


def test_get_feedback_requests_entry_by_id():
    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(_ENTRY)
        result = _service().get_feedback("feedback-1")

    assert (
        get.call_args.kwargs["url"] == "https://api.example.com/v1/feedback/feedback-1"
    )
    assert result.id == "feedback-1"
    assert result.comments == "Not helpful"
