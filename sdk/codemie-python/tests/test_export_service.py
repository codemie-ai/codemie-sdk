"""Unit tests for the export service (GET /v1/export/{kind}/{id})."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from codemie_sdk.services.export import ExportService

_DOCUMENT = {
    "version": "v1",
    "meta": {"kind": "assistant", "name": "a"},
    "spec": {"name": "a"},
}


def _ok(body: dict, status_code: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.content = b"1"
    response.json.return_value = body
    return response


def _error(status_code: int, body: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.content = b"1"
    response.json.return_value = body
    response.raise_for_status.side_effect = requests.HTTPError(response=response)
    return response


@pytest.fixture
def service():
    return ExportService("https://api.example.com", "token")


class TestExport:
    def test_returns_raw_document(self, service):
        with patch("codemie_sdk.utils.http.requests.get") as get:
            get.return_value = _ok(_DOCUMENT)
            result = service.export("assistant", "assistant-1")

        assert get.call_args.kwargs["url"].endswith("/v1/export/assistant/assistant-1")
        assert result == _DOCUMENT

    def test_returns_document_unwrapped_when_it_has_a_top_level_data_key(self, service):
        # ApiRequestHandler._parse_response unwraps a top-level `data` key by default. The
        # export document has no such key today, but if it ever grows one, export() must
        # still hand back the whole document, not the inner `data` value.
        document_with_data_key = {**_DOCUMENT, "data": "not the real document"}
        with patch("codemie_sdk.utils.http.requests.get") as get:
            get.return_value = _ok(document_with_data_key)
            result = service.export("assistant", "assistant-1")

        assert result == document_with_data_key

    def test_raises_http_error_on_failure(self, service):
        body = {"error": {"message": "Unknown export kind 'bogus'", "details": None}}
        with patch("codemie_sdk.utils.http.requests.get") as get:
            get.return_value = _error(404, body)
            with pytest.raises(requests.HTTPError) as exc_info:
                service.export("bogus", "abc")

        assert exc_info.value.response.status_code == 404
        assert exc_info.value.response.json() == body


class TestExportRaw:
    def test_returns_exact_response_bytes(self, service):
        body = b'{"version":"v1","meta":{"kind":"assistant","name":"a"},"spec":{"name":"a"}}'
        response = MagicMock()
        response.status_code = 200
        response.content = body
        with patch("codemie_sdk.utils.http.requests.get") as get:
            get.return_value = response
            result = service.export_raw("assistant", "assistant-1")

        assert result == body

    def test_raises_http_error_on_failure(self, service):
        with patch("codemie_sdk.utils.http.requests.get") as get:
            get.return_value = _error(
                422, {"error": {"message": "nope", "details": None}}
            )
            with pytest.raises(requests.HTTPError):
                service.export_raw("assistant", "assistant-1")
