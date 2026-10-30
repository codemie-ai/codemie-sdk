from codemie_sdk.models.assistant import MCPServerDetails
from codemie_sdk.models.skill import (
    SkillCreateRequest,
    SkillDetailResponse,
    SkillUpdateRequest,
    SkillVisibility,
)


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


_TOOLKITS = [{"toolkit": "Git", "tools": [{"name": "x"}]}]

_DETAIL = {
    "id": "skill-1",
    "name": "s",
    "description": "d",
    "project": "p",
    "visibility": "project",
    "createdDate": "2026-09-24T00:00:00Z",
    "content": "c",
}


def test_skill_detail_response_keeps_toolkits():
    response = SkillDetailResponse.model_validate({**_DETAIL, "toolkits": _TOOLKITS})
    assert response.toolkits == _TOOLKITS


def test_skill_update_request_includes_toolkits():
    request = SkillUpdateRequest(toolkits=_TOOLKITS)
    assert request.model_dump(exclude_none=True)["toolkits"] == _TOOLKITS


def test_skill_toolkits_round_trip_from_read_to_update():
    response = SkillDetailResponse.model_validate({**_DETAIL, "toolkits": _TOOLKITS})
    request = SkillUpdateRequest(toolkits=response.toolkits)
    assert request.model_dump(exclude_none=True)["toolkits"] == _TOOLKITS


def test_skill_empty_toolkits_are_sent():
    update = SkillUpdateRequest(toolkits=[])
    assert update.model_dump(exclude_none=True)["toolkits"] == []
    create = SkillCreateRequest(
        name="s", description="d", content="c", project="p", toolkits=[]
    )
    assert create.model_dump(exclude_none=True)["toolkits"] == []


def test_skill_toolkits_none_is_omitted_and_existing_dumps_unchanged():
    assert "toolkits" not in SkillUpdateRequest(name="s").model_dump(exclude_none=True)
    create = SkillCreateRequest(name="s", description="d", content="c", project="p")
    assert "toolkits" not in create.model_dump(exclude_none=True)
    assert SkillDetailResponse.model_validate(_DETAIL).toolkits is None