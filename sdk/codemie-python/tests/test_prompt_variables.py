from types import SimpleNamespace
from codemie_sdk.services.assistant import AssistantService
from codemie_sdk.models.assistant import (
    AssistantCreateRequest,
    AssistantUpdateRequest,
    PromptVariable,
)


class DummyApi:
    def __init__(self):
        self.last_call = SimpleNamespace(endpoint=None, json_data=None, method=None)

    def post(
        self, endpoint, response_model, json_data=None, stream=False, wrap_response=True
    ):
        self.last_call.endpoint = endpoint
        self.last_call.json_data = json_data
        self.last_call.method = "POST"
        return {"ok": True}

    def put(
        self, endpoint, response_model, json_data=None, stream=False, wrap_response=True
    ):
        self.last_call.endpoint = endpoint
        self.last_call.json_data = json_data
        self.last_call.method = "PUT"
        return {"ok": True}


def test_create_passes_prompt_variables():
    service = AssistantService("https://api.example.com", "token")
    dummy_api = DummyApi()
    service._api = dummy_api

    req = AssistantCreateRequest(
        name="PV Assistant",
        description="Assistant with prompt vars",
        system_prompt="You are helpful",
        project="demo",
        llm_model_type="gpt-4o",
        context=[],
        toolkits=[],
        conversation_starters=[],
        mcp_servers=[],
        assistant_ids=[],
        prompt_variables=[
            PromptVariable(
                key="project_name", default_value="Demo", description="Project name"
            ),
            PromptVariable(key="region", default_value="eu"),
        ],
    )

    service.create(req)

    assert dummy_api.last_call.endpoint == "/v1/assistants"
    body = dummy_api.last_call.json_data
    assert isinstance(body.get("prompt_variables"), list)
    assert body["prompt_variables"][0]["key"] == "project_name"
    assert body["prompt_variables"][1]["default_value"] == "eu"


def test_prompt_variable_is_sensitive_defaults_to_false():
    variable = PromptVariable(key="region", default_value="eu")

    assert variable.is_sensitive is False


def test_prompt_variable_parses_is_sensitive_from_response():
    variable = PromptVariable.model_validate(
        {"key": "api_key", "default_value": "********", "is_sensitive": True}
    )

    assert variable.is_sensitive is True


def test_create_passes_is_sensitive():
    service = AssistantService("https://api.example.com", "token")
    dummy_api = DummyApi()
    service._api = dummy_api

    req = AssistantCreateRequest(
        name="PV Assistant",
        description="Assistant with prompt vars",
        system_prompt="You are helpful",
        project="demo",
        llm_model_type="gpt-4o",
        context=[],
        toolkits=[],
        conversation_starters=[],
        mcp_servers=[],
        assistant_ids=[],
        prompt_variables=[
            PromptVariable(key="api_key", default_value="secret", is_sensitive=True),
            PromptVariable(key="region", default_value="eu"),
        ],
    )

    service.create(req)

    body = dummy_api.last_call.json_data
    assert body["prompt_variables"][0]["is_sensitive"] is True
    assert body["prompt_variables"][1]["is_sensitive"] is False


def test_update_passes_is_sensitive():
    service = AssistantService("https://api.example.com", "token")
    dummy_api = DummyApi()
    service._api = dummy_api

    req = AssistantUpdateRequest(
        name="PV Assistant",
        description="Assistant with prompt vars",
        system_prompt="Updated",
        project="demo",
        llm_model_type="gpt-4o",
        context=[],
        toolkits=[],
        conversation_starters=[],
        mcp_servers=[],
        assistant_ids=[],
        prompt_variables=[
            PromptVariable(key="api_key", default_value="secret", is_sensitive=True),
        ],
    )

    service.update("assistant-123", req)

    body = dummy_api.last_call.json_data
    assert body["prompt_variables"][0]["is_sensitive"] is True


def test_update_passes_prompt_variables():
    service = AssistantService("https://api.example.com", "token")
    dummy_api = DummyApi()
    service._api = dummy_api

    req = AssistantUpdateRequest(
        name="PV Assistant",
        description="Assistant with prompt vars",
        system_prompt="Updated",
        project="demo",
        llm_model_type="gpt-4o",
        context=[],
        toolkits=[],
        conversation_starters=[],
        mcp_servers=[],
        assistant_ids=[],
        prompt_variables=[
            PromptVariable(key="project_name", default_value="Demo-2"),
        ],
    )

    service.update("assistant-123", req)

    assert dummy_api.last_call.endpoint == "/v1/assistants/assistant-123"
    body = dummy_api.last_call.json_data
    assert isinstance(body.get("prompt_variables"), list)
    assert body["prompt_variables"][0]["default_value"] == "Demo-2"
