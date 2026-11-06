"""Tests for ApiRequestHandler/AssistantService streaming response parsing.

stream=True must return a typed BaseModelResponse so `.generated` works
directly (the originally reported bug), while also surviving the two
real-world cases a raw platform stream can produce: a multi-byte character
split across network chunks, and a tool-call interruption whose terminal
chunk carries no `generated` value at all.
"""

from typing import Any, Optional
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from codemie_sdk.exceptions import IncompleteStreamError
from codemie_sdk.models.assistant import AssistantChatRequest, BaseModelResponse
from codemie_sdk.services.assistant import AssistantService
from codemie_sdk.utils.http import ApiRequestHandler


def _fake_stream_response(chunks: list[bytes]) -> MagicMock:
    """A requests.Response stand-in whose iter_content() is called twice:
    once to read up to the terminal chunk, once more to drain the rest."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.close = MagicMock()
    resp.iter_content = MagicMock(side_effect=[iter(chunks), iter([])])
    return resp


def _handler() -> ApiRequestHandler:
    return ApiRequestHandler(base_url="https://codemie.example.com", token="tok")


class TestConsumeStream:
    def test_handles_concatenated_json_with_no_separators(self):
        """The server sends back-to-back JSON objects with no newline between
        them; raw_decode must split them without raising JSONDecodeError."""
        handler = _handler()
        chunk = (
            '{"generated": "thinking", "success": null, "last": false}'
            '{"generated": "final answer", "success": true, "last": true}'
        ).encode("utf-8")
        response = _fake_stream_response([chunk])

        result = handler._consume_stream(response)

        assert result == {
            "generated": "final answer",
            "success": True,
            "last": True,
        }

    def test_handles_object_split_across_multiple_chunks(self):
        """A single JSON object arriving in fragments across iter_content
        calls must still be reassembled correctly."""
        handler = _handler()
        chunks = [
            b'{"genera',
            b'ted": "hel',
            b'lo", "success": true, "last": true}',
        ]
        response = _fake_stream_response(chunks)

        result = handler._consume_stream(response)

        assert result == {"generated": "hello", "success": True, "last": True}

    def test_handles_multibyte_character_split_across_chunks(self):
        """A UTF-8 character (e.g. Cyrillic) split mid-sequence across two
        network chunks must be decoded correctly, not raise
        UnicodeDecodeError. Regression test for a reviewer-reported bug."""
        handler = _handler()
        payload = '{"generated": "Привет", "success": true, "last": true}'
        raw = payload.encode("utf-8")
        split_point = raw.index(b"\xd0", 1) + 1  # split inside a 2-byte sequence
        chunks = [raw[:split_point], raw[split_point:]]
        response = _fake_stream_response(chunks)

        result = handler._consume_stream(response)

        assert result == {
            "generated": "Привет",
            "success": True,
            "last": True,
        }

    def test_stops_at_terminal_chunk_and_drains_the_rest(self):
        """Once "last": true is seen, the rest of the stream must be drained
        and the connection closed rather than left half-read."""
        handler = _handler()
        chunk = b'{"generated": "done", "success": true, "last": true}'
        response = _fake_stream_response([chunk])

        handler._consume_stream(response)

        assert response.iter_content.call_count == 2  # one read + one drain
        response.close.assert_called_once()

    def test_terminal_chunk_without_generated_does_not_crash(self):
        """A tool-call interruption ends the stream with `generated` absent
        and no `last: true` answer payload; _consume_stream must still
        return the terminal chunk as-is."""
        handler = _handler()
        chunk = b'{"thought": {"interrupted": true}, "generated": null, "last": true}'
        response = _fake_stream_response([chunk])

        result = handler._consume_stream(response)

        assert result["generated"] is None
        assert result["last"] is True

    def test_connection_dropped_before_last_chunk_raises(self):
        """If the stream ends without ever seeing a `"last": true` chunk
        (dropped connection, truncated response), _consume_stream must raise
        rather than silently return an incomplete/empty chunk — otherwise a
        truncated connection is indistinguishable from a legitimate
        tool-call interruption once parsed into BaseModelResponse."""
        handler = _handler()
        chunk = b'{"generated": "partial thinking...", "last": false}'
        response = _fake_stream_response([chunk])

        with pytest.raises(IncompleteStreamError):
            handler._consume_stream(response)

    def test_connection_dropped_with_no_chunk_at_all_raises(self):
        """An empty/dropped stream with zero parseable JSON must also raise,
        not silently return `{}`."""
        handler = _handler()
        response = _fake_stream_response([])

        with pytest.raises(IncompleteStreamError):
            handler._consume_stream(response)


class TestPostStreamTrue:
    def test_returns_parsed_base_model_response(self):
        """stream=True must return a typed BaseModelResponse, not the raw
        requests.Response."""
        handler = _handler()
        chunk = b'{"generated": "hello world", "success": true, "last": true}'

        with patch("requests.post", return_value=_fake_stream_response([chunk])):
            result = handler.post(
                "/v1/assistants/a1/model",
                BaseModelResponse,
                json_data={"text": "hi"},
                stream=True,
            )

        assert isinstance(result, BaseModelResponse)
        assert result.generated == "hello world"

    def test_interrupted_stream_parses_with_generated_none(self):
        """A tool-call-interruption terminal chunk (no generated value) must
        parse into a BaseModelResponse with generated=None instead of
        raising ValidationError, so callers can detect the pause and call
        resume_tool_call."""
        handler = _handler()
        chunk = b'{"thought": {"interrupted": true}, "generated": null, "last": true}'

        with patch("requests.post", return_value=_fake_stream_response([chunk])):
            result = handler.post(
                "/v1/assistants/a1/model",
                BaseModelResponse,
                json_data={"text": "hi"},
                stream=True,
            )

        assert isinstance(result, BaseModelResponse)
        assert result.generated is None

    def test_non_pydantic_response_model_returns_raw_response_unconsumed(self):
        """export() passes response_model=Any with stream=True, and
        resume_tool_call passes requests.Response; both must get the raw,
        unconsumed response back so the caller can read the stream itself."""
        handler = _handler()
        raw_response = _fake_stream_response([b"irrelevant"])

        with patch("requests.post", return_value=raw_response):
            result = handler.post(
                "/v1/assistants/a1/export",
                Any,
                stream=True,
            )

        assert result is raw_response
        raw_response.iter_content.assert_not_called()

    def test_stream_false_still_returns_parsed_base_model_response(self):
        """Sanity check that the streaming branch doesn't disturb the
        existing non-streaming parse path."""
        handler = _handler()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.content = b'{"generated": "non-stream", "success": true}'
        mock_response.json.return_value = {
            "generated": "non-stream",
            "success": True,
        }

        with patch("requests.post", return_value=mock_response):
            result = handler.post(
                "/v1/assistants/a1/model",
                BaseModelResponse,
                json_data={"text": "hi"},
                stream=False,
            )

        assert isinstance(result, BaseModelResponse)
        assert result.generated == "non-stream"
        mock_response.iter_content.assert_not_called()

    def test_stream_true_with_optional_model_returns_parsed(self):
        """_extract_pydantic_model must unwrap Optional[Model] so a
        streamed Optional[BaseModelResponse] response is still parsed."""
        handler = _handler()
        chunk = b'{"generated": "hello", "success": true, "last": true}'

        with patch("requests.post", return_value=_fake_stream_response([chunk])):
            result = handler.post(
                "/v1/assistants/a1/model",
                Optional[BaseModelResponse],
                json_data={"text": "hi"},
                stream=True,
            )

        assert isinstance(result, BaseModelResponse)
        assert result.generated == "hello"

    def test_stream_true_with_list_model_returns_parsed_list(self):
        """_extract_pydantic_model must unwrap list[Model] so a streamed
        list[BaseModelResponse] response is still parsed into a list."""
        handler = _handler()
        chunk = b'{"generated": "hello", "success": true, "last": true}'

        with patch("requests.post", return_value=_fake_stream_response([chunk])):
            result = handler.post(
                "/v1/assistants/a1/model",
                list[BaseModelResponse],
                json_data={"text": "hi"},
                stream=True,
            )

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], BaseModelResponse)
        assert result[0].generated == "hello"


class TestAssistantServiceChat:
    def test_stream_true_exposes_generated_attribute(self):
        """chat(stream=True) must return an object whose .generated can be
        read directly, without the caller parsing the stream itself."""
        handler = _handler()
        svc = AssistantService.__new__(AssistantService)
        svc._api = handler
        chunk = b'{"generated": "6", "success": true, "last": true}'

        with patch("requests.post", return_value=_fake_stream_response([chunk])):
            response = svc.chat(
                "assistant-1", AssistantChatRequest(text="Hello", stream=True)
            )

        assert response.generated == "6"

    def test_stream_true_tool_call_interruption_does_not_raise(self):
        """chat(stream=True) must not raise when the assistant pauses for
        tool-call approval; callers detect the pause via generated is None
        and continue with resume_tool_call."""
        handler = _handler()
        svc = AssistantService.__new__(AssistantService)
        svc._api = handler
        chunk = b'{"thought": {"interrupted": true}, "generated": null, "last": true}'

        with patch("requests.post", return_value=_fake_stream_response([chunk])):
            response = svc.chat(
                "assistant-1", AssistantChatRequest(text="Hello", stream=True)
            )

        assert response.generated is None

    def test_stream_true_with_output_schema_converts_generated_to_the_model(self):
        """output_schema conversion must run for streaming responses too,
        parsing the JSON-string form the real platform stream sends for the
        terminal chunk's `generated` field (unlike the non-streaming path,
        which returns it already parsed as a dict)."""

        class Answer(BaseModel):
            value: int

        handler = _handler()
        svc = AssistantService.__new__(AssistantService)
        svc._api = handler
        chunk = b'{"generated": "{\\"value\\": 42}", "success": true, "last": true}'

        with patch("requests.post", return_value=_fake_stream_response([chunk])):
            response = svc.chat(
                "assistant-1",
                AssistantChatRequest(text="Hello", stream=True, output_schema=Answer),
            )

        assert isinstance(response.generated, Answer)
        assert response.generated.value == 42

    def test_stream_false_with_output_schema_converts_generated_dict_to_the_model(
        self,
    ):
        """The non-streaming path still receives `generated` already parsed
        as a dict and must keep converting it via model_validate."""

        class Answer(BaseModel):
            value: int

        handler = _handler()
        svc = AssistantService.__new__(AssistantService)
        svc._api = handler
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.content = b'{"generated": {"value": 42}, "success": true}'
        mock_response.json.return_value = {
            "generated": {"value": 42},
            "success": True,
        }

        with patch("requests.post", return_value=mock_response):
            response = svc.chat(
                "assistant-1",
                AssistantChatRequest(text="Hello", output_schema=Answer),
            )

        assert isinstance(response.generated, Answer)
        assert response.generated.value == 42

    def test_stream_true_tool_call_interruption_with_output_schema_skips_conversion(
        self,
    ):
        """When the stream ends on a tool-call interruption (generated is
        None), output_schema conversion must be skipped rather than crash
        on a None value."""

        class Answer(BaseModel):
            value: int

        handler = _handler()
        svc = AssistantService.__new__(AssistantService)
        svc._api = handler
        chunk = b'{"thought": {"interrupted": true}, "generated": null, "last": true}'

        with patch("requests.post", return_value=_fake_stream_response([chunk])):
            response = svc.chat(
                "assistant-1",
                AssistantChatRequest(text="Hello", stream=True, output_schema=Answer),
            )

        assert response.generated is None
