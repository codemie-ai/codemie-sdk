"""Unit tests for ProjectService.project_exists."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
import requests

from codemie_sdk.services.project import ProjectService

_DETAIL = dict(
    name="p",
    project_type="shared",
    created_by="u",
    created_at=datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
    user_count=0,
    admin_count=0,
    members=[],
)


@pytest.fixture
def service():
    return ProjectService("https://api.example.com", "token")


def _response(status):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = _DETAIL
    if status >= 400:
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=response
        )
    return response


def test_project_exists_true_on_200(service):
    with patch("codemie_sdk.utils.http.requests.get", return_value=_response(200)):
        assert service.project_exists("p") is True


def test_project_exists_false_on_404(service):
    with patch("codemie_sdk.utils.http.requests.get", return_value=_response(404)):
        assert service.project_exists("p") is False


@pytest.mark.parametrize("status", [401, 500])
def test_project_exists_raises_on_other_http_errors(service, status):
    with patch("codemie_sdk.utils.http.requests.get", return_value=_response(status)):
        with pytest.raises(requests.exceptions.HTTPError):
            service.project_exists("p")


def test_project_exists_raises_on_connection_error(service):
    with patch(
        "codemie_sdk.utils.http.requests.get",
        side_effect=requests.exceptions.ConnectionError,
    ):
        with pytest.raises(requests.exceptions.ConnectionError):
            service.project_exists("p")
