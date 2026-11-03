"""Unit tests for UserService.reactivate_user."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from codemie_sdk.models.user import CodeMieUserDetail
from codemie_sdk.services.user import UserService

_USER = dict(
    id="u1",
    username="jane",
    email="jane@example.com",
    is_active=True,
    is_admin=False,
)


@pytest.fixture
def service():
    return UserService("https://api.example.com", "token")


def _response(status_code, body=None):
    response = MagicMock()
    response.status_code = status_code
    response.content = b"{}"
    response.json.return_value = body or {}
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(
            response=response
        )
    return response


def test_reactivate_user_posts_without_body_and_parses_user(service):
    with patch(
        "codemie_sdk.utils.http.requests.post", return_value=_response(200, _USER)
    ) as post:
        user = service.reactivate_user("u1")

    assert post.call_args.kwargs["url"] == (
        "https://api.example.com/v1/admin/users/u1/reactivate"
    )
    assert post.call_args.kwargs["json"] is None
    assert post.call_args.kwargs["data"] is None
    assert isinstance(user, CodeMieUserDetail)
    assert user.id == "u1" and user.is_active is True


@pytest.mark.parametrize("status_code", [403, 404, 409])
def test_reactivate_user_propagates_http_errors(service, status_code):
    with patch(
        "codemie_sdk.utils.http.requests.post", return_value=_response(status_code)
    ):
        with pytest.raises(requests.HTTPError) as exc:
            service.reactivate_user("u1")

    assert exc.value.response.status_code == status_code
