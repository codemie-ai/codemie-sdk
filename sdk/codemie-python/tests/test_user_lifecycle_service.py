# Copyright 2026 EPAM Systems, Inc. ("EPAM")
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for the user deactivate / reactivate service calls."""

from unittest.mock import MagicMock, patch

import pytest

from codemie_sdk.models.user import CodeMieUserDetail
from codemie_sdk.services.user import UserService

_USER = {
    "id": "user-1",
    "username": "jane",
    "email": "jane@example.com",
    "is_active": True,
    "is_admin": False,
}


def _ok(body: dict, status_code: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = body
    return response


@pytest.fixture
def service():
    return UserService("https://api.example.com", "token")


class TestReactivate:
    def test_posts_to_reactivate_path_and_returns_user_detail(self, service):
        with patch("codemie_sdk.utils.http.requests.post") as post:
            post.return_value = _ok(_USER)
            result = service.reactivate_user("user-1")

        assert post.call_args.kwargs["url"].endswith(
            "/v1/admin/users/user-1/reactivate"
        )
        assert post.call_args.kwargs["json"] is None
        assert isinstance(result, CodeMieUserDetail)
        assert result.id == "user-1"
        assert result.is_active is True

    def test_does_not_send_put(self, service):
        with (
            patch("codemie_sdk.utils.http.requests.post") as post,
            patch("codemie_sdk.utils.http.requests.put") as put,
        ):
            post.return_value = _ok(_USER)
            service.reactivate_user("user-1")

        put.assert_not_called()


class TestDeactivate:
    def test_deletes_user_and_returns_response_body(self, service):
        body = {"message": "User deactivated successfully"}
        with patch("codemie_sdk.utils.http.requests.delete") as delete:
            delete.return_value = _ok(body)
            result = service.deactivate_user("user-1")

        assert delete.call_args.kwargs["url"].endswith("/v1/admin/users/user-1")
        assert result == body
