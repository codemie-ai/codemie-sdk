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

"""Unit tests for the global MCP configs service (list, clone, update)."""

from unittest.mock import MagicMock, patch

import pytest

from codemie_sdk.models.mcp_config import (
    MCPConfigCloneRequest,
    MCPConfigListResponse,
    MCPConfigResponse,
    MCPConfigUpdateRequest,
    MCPServerConfigData,
)
from codemie_sdk.services.mcp_configs import MCPConfigsService

_CONFIG = {"id": "cfg-1", "name": "server-a", "is_public": True, "is_system": False}


def _ok(body: dict, status_code: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = body
    return response


@pytest.fixture
def service():
    return MCPConfigsService("https://api.example.com", "token")


class TestListResponse:
    def test_reads_configs_key(self):
        parsed = MCPConfigListResponse(configs=[_CONFIG], total=1, page=0, per_page=20)
        assert [c.id for c in parsed.configs] == ["cfg-1"]

    def test_unknown_data_key_is_ignored(self):
        assert MCPConfigListResponse(data=[_CONFIG]).configs == []


class TestList:
    def test_returns_configs_from_response(self, service):
        body = {"configs": [_CONFIG], "total": 1, "page": 0, "per_page": 100}
        with patch("codemie_sdk.utils.http.requests.get") as get:
            get.return_value = _ok(body)
            result = service.list(per_page=100, search="server-a")

        assert [c.id for c in result] == ["cfg-1"]
        assert get.call_args.kwargs["params"] == {
            "page": 0,
            "per_page": 100,
            "search": "server-a",
        }

    def test_empty_page_returns_empty_list(self, service):
        body = {"configs": [], "total": 0, "page": 0, "per_page": 20}
        with patch("codemie_sdk.utils.http.requests.get") as get:
            get.return_value = _ok(body)
            assert service.list() == []


class TestClone:
    def test_posts_form_payload_to_clone_endpoint(self, service):
        request = MCPConfigCloneRequest(
            name="server-a-copy",
            description="edited",
            categories=["AI"],
            config=MCPServerConfigData(url="https://mcp.example.com/mcp"),
        )
        with patch("codemie_sdk.utils.http.requests.post") as post:
            post.return_value = _ok(
                dict(_CONFIG, id="cfg-2", name="server-a-copy"), 201
            )
            result = service.clone("cfg-1", request)

        assert post.call_args.kwargs["url"].endswith("/v1/mcp-configs/cfg-1/clone")
        sent = post.call_args.kwargs["json"]
        assert sent["name"] == "server-a-copy"
        assert sent["categories"] == ["AI"]
        assert sent["config"]["url"] == "https://mcp.example.com/mcp"
        assert isinstance(result, MCPConfigResponse)
        assert result.id == "cfg-2"

    def test_request_has_no_visibility_fields(self):
        fields = MCPConfigCloneRequest.model_fields
        assert "is_public" not in fields
        assert "is_system" not in fields


class TestUpdate:
    def test_puts_only_provided_fields(self, service):
        with patch("codemie_sdk.utils.http.requests.put") as put:
            put.return_value = _ok(dict(_CONFIG, description="changed"))
            result = service.update(
                "cfg-1", MCPConfigUpdateRequest(description="changed")
            )

        assert put.call_args.kwargs["url"].endswith("/v1/mcp-configs/cfg-1")
        assert put.call_args.kwargs["json"] == {"description": "changed"}
        assert result.id == "cfg-1"

    def test_false_flag_is_sent(self, service):
        with patch("codemie_sdk.utils.http.requests.put") as put:
            put.return_value = _ok(dict(_CONFIG, is_public=False))
            service.update("cfg-1", MCPConfigUpdateRequest(is_public=False))

        assert put.call_args.kwargs["json"] == {"is_public": False}
