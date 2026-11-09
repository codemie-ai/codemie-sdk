"""Unit tests for project-level cli_analytics_enabled in SDK models and service."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from codemie_sdk.models.project import (
    ProjectCreateRequest,
    ProjectCreateResponse,
    ProjectDetailResponse,
    ProjectListItem,
    ProjectUpdateRequest,
)
from codemie_sdk.services.project import ProjectService

_LIST = dict(name="p", project_type="shared", user_count=0, admin_count=0)
_DETAIL = dict(_LIST, members=[])
_CREATE = dict(
    name="p",
    project_type="shared",
    created_by="u",
    created_at=datetime(2026, 1, 1, tzinfo=UTC),
)

_RESPONSE_MODELS = [
    (ProjectListItem, _LIST),
    (ProjectDetailResponse, _DETAIL),
    (ProjectCreateResponse, _CREATE),
]


@pytest.mark.parametrize("model,base", _RESPONSE_MODELS)
class TestResponseModels:
    def test_absent_key_is_none_not_false(self, model, base):
        assert model(**base).cli_analytics_enabled is None

    def test_false_is_kept(self, model, base):
        assert model(**base, cli_analytics_enabled=False).cli_analytics_enabled is False

    def test_true_is_kept(self, model, base):
        assert model(**base, cli_analytics_enabled=True).cli_analytics_enabled is True


class TestRequestModels:
    def test_create_request_default_none(self):
        assert ProjectCreateRequest(name="p").cli_analytics_enabled is None

    def test_update_request_default_none(self):
        assert ProjectUpdateRequest().cli_analytics_enabled is None

    def test_false_survives_exclude_none(self):
        dumped = ProjectUpdateRequest(cli_analytics_enabled=False).model_dump(
            exclude_none=True
        )
        assert dumped["cli_analytics_enabled"] is False


def _ok(body: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = body
    return response


@pytest.fixture
def service():
    return ProjectService("https://api.example.com", "token")


class TestUpdateProject:
    def test_false_is_sent(self, service):
        with patch("codemie_sdk.utils.http.requests.patch") as patch_req:
            patch_req.return_value = _ok(
                dict(_CREATE, created_at="2026-01-01T00:00:00Z")
            )
            service.update_project("p", cli_analytics_enabled=False)
        assert patch_req.call_args.kwargs["json"]["cli_analytics_enabled"] is False

    def test_true_is_sent(self, service):
        with patch("codemie_sdk.utils.http.requests.patch") as patch_req:
            patch_req.return_value = _ok(
                dict(_CREATE, created_at="2026-01-01T00:00:00Z")
            )
            service.update_project("p", cli_analytics_enabled=True)
        assert patch_req.call_args.kwargs["json"]["cli_analytics_enabled"] is True

    def test_omitted_leaves_key_out(self, service):
        with patch("codemie_sdk.utils.http.requests.patch") as patch_req:
            patch_req.return_value = _ok(
                dict(_CREATE, created_at="2026-01-01T00:00:00Z")
            )
            service.update_project("p", description="d")
        assert "cli_analytics_enabled" not in patch_req.call_args.kwargs["json"]


class TestCreateProject:
    def test_false_is_sent(self, service):
        with patch("codemie_sdk.utils.http.requests.post") as post:
            post.return_value = _ok(dict(_CREATE, created_at="2026-01-01T00:00:00Z"))
            service.create_project("p", cli_analytics_enabled=False)
        assert post.call_args.kwargs["json"]["cli_analytics_enabled"] is False

    def test_omitted_leaves_key_out(self, service):
        with patch("codemie_sdk.utils.http.requests.post") as post:
            post.return_value = _ok(dict(_CREATE, created_at="2026-01-01T00:00:00Z"))
            service.create_project("p")
        assert "cli_analytics_enabled" not in post.call_args.kwargs["json"]
