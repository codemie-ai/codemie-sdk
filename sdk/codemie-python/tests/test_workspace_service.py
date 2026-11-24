"""Unit tests for the workspace service download call (GET /v1/workspaces/{id}/files/download)."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from codemie_sdk.services.workspace import WorkspaceService


@pytest.fixture
def service():
    return WorkspaceService("https://api.example.com", "token")


class TestDownloadFile:
    def test_returns_exact_response_bytes(self, service):
        response = MagicMock()
        response.status_code = 200
        response.content = b"\x00raw bytes\xff"

        with patch("codemie_sdk.utils.http.requests.get") as get:
            get.return_value = response
            result = service.download_file("ws-1", "notes/a.txt")

        assert get.call_args.kwargs["url"].endswith(
            "/v1/workspaces/ws-1/files/download"
        )
        assert get.call_args.kwargs["params"] == {"file_path": "notes/a.txt"}
        assert result == b"\x00raw bytes\xff"

    def test_raises_http_error_on_failure(self, service):
        response = MagicMock()
        response.status_code = 400
        response.raise_for_status.side_effect = requests.HTTPError(response=response)

        with patch("codemie_sdk.utils.http.requests.get") as get:
            get.return_value = response
            with pytest.raises(requests.HTTPError):
                service.download_file("ws-1", "notes/a.txt")
