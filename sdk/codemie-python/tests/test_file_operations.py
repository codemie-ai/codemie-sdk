"""Tests for FileOperationService.get_file_by_url() and the typed return
value of AssistantService.upload_file_to_chat()."""

import pytest

from codemie_sdk.models.file_operation import FileResponse
from codemie_sdk.services.assistant import AssistantService
from codemie_sdk.services.files import FileOperationService


def _service_with_spy_get_file():
    svc = FileOperationService.__new__(FileOperationService)
    calls = []

    def fake_get_file(file_id, share_token=None):
        calls.append(file_id)
        return b"file-bytes"

    svc.get_file = fake_get_file
    return svc, calls


class TestGetFileByUrl:
    def test_extracts_id_from_a_plain_url(self):
        svc, calls = _service_with_spy_get_file()

        result = svc.get_file_by_url("https://codemie.example.com/v1/files/abc123")

        assert calls == ["abc123"]
        assert result == b"file-bytes"

    def test_handles_trailing_slash(self):
        svc, calls = _service_with_spy_get_file()

        svc.get_file_by_url("https://codemie.example.com/v1/files/abc123/")

        assert calls == ["abc123"]

    def test_strips_query_string(self):
        """A naive rsplit("/") would leave "?x=1" glued to the id."""
        svc, calls = _service_with_spy_get_file()

        svc.get_file_by_url("https://codemie.example.com/v1/files/abc123?x=1&y=2")

        assert calls == ["abc123"]

    def test_strips_fragment(self):
        svc, calls = _service_with_spy_get_file()

        svc.get_file_by_url("https://codemie.example.com/v1/files/abc123#section")

        assert calls == ["abc123"]

    def test_raises_on_url_with_no_path_segment(self):
        svc, _ = _service_with_spy_get_file()

        with pytest.raises(ValueError, match="Could not extract file ID"):
            svc.get_file_by_url("https://codemie.example.com")


class TestUploadFileToChatReturnType:
    def test_returns_typed_file_response_not_a_dict(self, tmp_path):
        svc = AssistantService.__new__(AssistantService)
        captured = {}

        class _FakeApi:
            def post_multipart(self, endpoint, response_model, files=None):
                captured["response_model"] = response_model
                return FileResponse(file_url="https://codemie.example.com/v1/files/abc123")

        svc._api = _FakeApi()
        file_path = tmp_path / "note.txt"
        file_path.write_text("hello")

        result = svc.upload_file_to_chat(file_path)

        assert captured["response_model"] is FileResponse
        assert isinstance(result, FileResponse)
        assert result.file_url == "https://codemie.example.com/v1/files/abc123"
