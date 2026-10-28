"""Tests for AssistantChatRequest/VirtualAssistantChatRequest.conversation_id
defaulting and payload serialization."""

from codemie_sdk.models.assistant import (
    AssistantChatRequest,
    VirtualAssistantChatRequest,
)


class TestAssistantChatRequestConversationId:
    def test_defaults_to_none(self):
        request = AssistantChatRequest(text="hi")

        assert request.conversation_id is None

    def test_excluded_from_payload_when_none(self):
        request = AssistantChatRequest(text="hi")

        payload = request.model_dump(exclude_none=True, by_alias=True)

        assert "conversation_id" not in payload

    def test_explicit_value_is_preserved_and_sent(self):
        request = AssistantChatRequest(text="hi", conversation_id="session-123")

        payload = request.model_dump(exclude_none=True, by_alias=True)

        assert payload["conversation_id"] == "session-123"

    def test_separate_requests_without_an_explicit_id_do_not_diverge(self):
        first_turn = AssistantChatRequest(text="turn 1")
        second_turn = AssistantChatRequest(text="turn 2")

        assert first_turn.conversation_id is None
        assert second_turn.conversation_id is None

    def test_reusing_the_same_id_across_turns_keeps_it_identical(self):
        session_id = "session-abc"
        first_turn = AssistantChatRequest(text="turn 1", conversation_id=session_id)
        second_turn = AssistantChatRequest(text="turn 2", conversation_id=session_id)

        assert first_turn.conversation_id == second_turn.conversation_id == session_id


class TestVirtualAssistantChatRequestConversationId:
    def test_defaults_to_none(self):
        request = VirtualAssistantChatRequest()

        assert request.conversation_id is None

    def test_explicit_value_is_preserved(self):
        request = VirtualAssistantChatRequest(conversation_id="session-xyz")

        assert request.conversation_id == "session-xyz"
