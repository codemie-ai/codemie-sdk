"""File operation service implementation."""

import mimetypes
from pathlib import Path
from urllib.parse import urlparse

from ..models.file_operation import FileBulkCreateResponse
from ..utils import ApiRequestHandler, TokenSource


class FileOperationService:
    """Service for managing file operations."""

    def __init__(self, api_domain: str, token: TokenSource, verify_ssl: bool = True):
        """Initialize the file operation service.

        Args:
            api_domain: Base URL for the CodeMie API
            token: Authentication token
            verify_ssl: Whether to verify SSL certificates
        """
        self._api = ApiRequestHandler(api_domain, token, verify_ssl)

    def bulk_upload(self, files: list[Path]) -> FileBulkCreateResponse:
        """Upload multiple files in a single operation.

        Args:
            files: List of File paths (required)

        Returns:
            FileBulkCreateResponse: Results of the bulk operation including

        Raises:
            ValueError: If items in files is not a Path
            ApiError: If bulk creation fails or validation errors occur
        """

        files_to_upload = []

        for file_path in files:
            if isinstance(file_path, Path):
                # File path provided - read file and detect MIME type
                with open(file_path, "rb") as file:
                    content = file.read()

                # Basic MIME type detection
                mime_type = (
                    mimetypes.guess_type(file_path.name)[0]
                    or "application/octet-stream"
                )
                files_to_upload.append(("files", (file_path.name, content, mime_type)))
            else:
                raise ValueError("Each item in list must be a Path")

        response = self._api.post_multipart(
            "/v1/files/bulk",
            files=files_to_upload,
            response_model=FileBulkCreateResponse,
        )

        return response

    def get_file(self, file_id: str, share_token: str | None = None) -> bytes:
        """Get a file by its ID.

        Args:
            file_id: The file identifier (base64 encoded ID from file_url)
            share_token: Token of a shared conversation the file belongs to;
                grants access to the file for users who do not own it

        Returns:
            bytes: The file content as binary data

        Raises:
            ApiError: If the file doesn't exist or there's an API error
        """
        import requests

        response = self._api.get(
            f"/v1/files/{file_id}",
            response_model=requests.Response,
            params={"share_token": share_token} if share_token else None,
            wrap_response=False,
        )
        return response.content

    def get_file_by_url(self, url: str) -> bytes:
        """Download a file using the full URL from an assistant response.

        File URLs embedded in assistant responses (``/v1/files/<file_id>``)
        require bearer-token authentication. This method extracts the file_id
        and fetches the content with authentication.

        Args:
            url: Full file URL from an assistant response

        Returns:
            bytes: File content
        """
        file_id = urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
        if not file_id:
            raise ValueError(f"Could not extract file ID from URL: {url!r}")
        return self.get_file(file_id)
