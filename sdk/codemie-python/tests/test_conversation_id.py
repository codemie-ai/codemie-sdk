"""Tests for AssistantChatRequest/VirtualAssistantChatRequest.conversation_id
defaulting and payload serialization."""

from codemie_sdk.models.assistant import (
    AssistantChatRequest,
    VirtualAssistantChatRequest,
)


class TestAssistantChatRequestConversationId:
    def test_defaults_to_a_generated_uuid(self):
        request = AssistantChatRequest(text="hi")

        assert request.conversation_id is not None

    def test_generated_id_is_included_in_payload(self):
        request = AssistantChatRequest(text="hi")

        payload = request.model_dump(exclude_none=True, by_alias=True)

        assert payload["conversation_id"] == request.conversation_id

    def test_explicit_value_is_preserved_and_sent(self):
        request = AssistantChatRequest(text="hi", conversation_id="session-123")

        payload = request.model_dump(exclude_none=True, by_alias=True)

        assert payload["conversation_id"] == "session-123"

    def test_separate_instances_get_distinct_ids(self):
        first_turn = AssistantChatRequest(text="turn 1")
        second_turn = AssistantChatRequest(text="turn 2")

        assert first_turn.conversation_id != second_turn.conversation_id

    def test_reusing_the_same_request_object_keeps_the_id_across_turns(self):
        """Mutating and resending the same request instance (the documented
        multi-turn pattern) must keep one conversation_id across calls."""
        request = AssistantChatRequest(text="turn 1")
        first_id = request.conversation_id

        request.text = "turn 2"

        assert request.conversation_id == first_id

    def test_explicit_shared_id_across_two_instances_is_identical(self):
        session_id = "session-abc"
        first_turn = AssistantChatRequest(text="turn 1", conversation_id=session_id)
        second_turn = AssistantChatRequest(text="turn 2", conversation_id=session_id)

        assert first_turn.conversation_id == second_turn.conversation_id == session_id


class TestVirtualAssistantChatRequestConversationId:
    def test_defaults_to_a_generated_uuid(self):
        request = VirtualAssistantChatRequest()

        assert request.conversation_id is not None

    def test_explicit_value_is_preserved(self):
        request = VirtualAssistantChatRequest(conversation_id="session-xyz")

        assert request.conversation_id == "session-xyz"
