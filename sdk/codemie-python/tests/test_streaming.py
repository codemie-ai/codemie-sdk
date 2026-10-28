"""Tests for ApiRequestHandler/AssistantService streaming response parsing."""

from typing import Any, Optional
from unittest.mock import MagicMock, patch

from pydantic import BaseModel

from codemie_sdk.models.assistant import AssistantChatRequest, BaseModelResponse
from codemie_sdk.services.assistant import AssistantService
from codemie_sdk.utils.http import ApiRequestHandler


def _fake_stream_response(chunks: list[str]) -> MagicMock:
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
        )
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
        chunks = ['{"genera', 'ted": "hel', 'lo", "success": true, "last": true}']
        response = _fake_stream_response(chunks)

        result = handler._consume_stream(response)

        assert result == {"generated": "hello", "success": True, "last": True}

    def test_stops_at_terminal_chunk_and_drains_the_rest(self):
        """Once "last": true is seen, the rest of the stream must be drained
        and the connection closed rather than left half-read."""
        handler = _handler()
        chunk = '{"generated": "done", "success": true, "last": true}'
        response = _fake_stream_response([chunk])

        handler._consume_stream(response)

        assert response.iter_content.call_count == 2  # one read + one drain
        response.close.assert_called_once()


class TestPostStreamTrue:
    def test_returns_parsed_base_model_response(self):
        """stream=True must return a typed BaseModelResponse, not the raw
        requests.Response."""
        handler = _handler()
        chunk = '{"generated": "hello world", "success": true, "last": true}'

        with patch("requests.post", return_value=_fake_stream_response([chunk])):
            result = handler.post(
                "/v1/assistants/a1/model",
                BaseModelResponse,
                json_data={"text": "hi"},
                stream=True,
            )

        assert isinstance(result, BaseModelResponse)
        assert result.generated == "hello world"

    def test_non_pydantic_response_model_returns_raw_response_unconsumed(self):
        """export() passes response_model=Any with stream=True and must get
        the raw, unconsumed response back so it can read the file stream
        itself."""
        handler = _handler()
        raw_response = _fake_stream_response(["irrelevant"])

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
        chunk = '{"generated": "hello", "success": true, "last": true}'

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
        chunk = '{"generated": "hello", "success": true, "last": true}'

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
        chunk = '{"generated": "6", "success": true, "last": true}'

        with patch("requests.post", return_value=_fake_stream_response([chunk])):
            response = svc.chat(
                "assistant-1", AssistantChatRequest(text="Hello", stream=True)
            )

        assert response.generated == "6"

    def test_stream_true_with_output_schema_converts_generated_to_the_model(self):
        """output_schema conversion must run for streaming responses too,
        not only when stream=False."""

        class Answer(BaseModel):
            value: int

        handler = _handler()
        svc = AssistantService.__new__(AssistantService)
        svc._api = handler
        chunk = '{"generated": {"value": 42}, "success": true, "last": true}'

        with patch("requests.post", return_value=_fake_stream_response([chunk])):
            response = svc.chat(
                "assistant-1",
                AssistantChatRequest(text="Hello", stream=True, output_schema=Answer),
            )

        assert isinstance(response.generated, Answer)
        assert response.generated.value == 42
