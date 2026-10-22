from unittest.mock import patch

import pytest

from codemie_sdk.models.assistant import MCPServerDetails
from codemie_sdk.models.skill import (
    SkillCreateRequest,
    SkillDetailResponse,
    SkillImportRequest,
    SkillUpdateRequest,
    SkillVisibility,
)
from codemie_sdk.services.skill import SkillService


def _hand_written_server():
    return MCPServerDetails(name="custom-server", description=None, enabled=True)


def test_skill_create_request_accepts_mcp_servers():
    request = SkillCreateRequest(
        name="s",
        description="d",
        content="c",
        project="p",
        mcp_servers=[_hand_written_server()],
    )
    dumped = request.model_dump(exclude_none=True)
    assert dumped["mcp_servers"][0]["name"] == "custom-server"


def test_skill_update_request_omits_mcp_servers_when_unset():
    request = SkillUpdateRequest(name="s")
    assert "mcp_servers" not in request.model_dump(exclude_none=True)


def test_skill_update_request_accepts_mcp_servers_when_set():
    request = SkillUpdateRequest(mcp_servers=[_hand_written_server()])
    dumped = request.model_dump(exclude_none=True)
    assert dumped["mcp_servers"][0]["name"] == "custom-server"


def test_skill_detail_response_exposes_mcp_servers():
    response = SkillDetailResponse(
        id="skill-1",
        name="s",
        description="d",
        project="p",
        visibility=SkillVisibility.PROJECT,
        createdDate="2026-09-24T00:00:00Z",
        content="c",
        mcp_servers=[_hand_written_server()],
    )
    assert response.mcp_servers[0].name == "custom-server"


def _service_with_mock_api():
    with patch("codemie_sdk.services.skill.ApiRequestHandler") as handler_cls:
        service = SkillService("https://api.example.com", "token")
    return service, handler_cls.return_value


@pytest.mark.parametrize("visibility", [SkillVisibility.PROJECT, SkillVisibility.PUBLIC])
def test_skill_service_create_sends_visibility(visibility):
    service, api = _service_with_mock_api()
    service.create(
        SkillCreateRequest(
            name="s", description="d", content="c", project="p", visibility=visibility
        )
    )
    args, kwargs = api.post.call_args
    assert args[0] == "/v1/skills"
    assert kwargs["json_data"]["visibility"] == visibility.value


@pytest.mark.parametrize("visibility", [SkillVisibility.PROJECT, SkillVisibility.PUBLIC])
def test_skill_service_update_sends_visibility(visibility):
    service, api = _service_with_mock_api()
    service.update("s1", SkillUpdateRequest(visibility=visibility))
    args, kwargs = api.put.call_args
    assert args[0] == "/v1/skills/s1"
    assert kwargs["json_data"]["visibility"] == visibility.value


def test_skill_service_update_omits_visibility_when_unset():
    service, api = _service_with_mock_api()
    service.update("s1", SkillUpdateRequest(name="s"))
    _, kwargs = api.put.call_args
    assert "visibility" not in kwargs["json_data"]


@pytest.mark.parametrize("visibility", [SkillVisibility.PROJECT, SkillVisibility.PUBLIC])
def test_skill_service_import_sends_visibility(visibility):
    service, api = _service_with_mock_api()
    service.import_skill(
        SkillImportRequest(
            file_content="Zm9v", filename="s.md", project="p", visibility=visibility
        )
    )
    args, kwargs = api.post.call_args
    assert args[0] == "/v1/skills/import"
    assert kwargs["json_data"]["visibility"] == visibility.value
