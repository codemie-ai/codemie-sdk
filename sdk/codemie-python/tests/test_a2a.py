import pytest
import requests
from requests import HTTPError

from codemie_sdk.models.a2a import AgentCard
from codemie_sdk.services.a2a import A2AService

V1_CARD = {
    "name": "assistant",
    "description": "Integration test assistant",
    "supportedInterfaces": [
        {
            "url": "https://api.example.com/v1/a2a/assistants/a1",
            "protocolBinding": "JSONRPC",
            "protocolVersion": "1.0",
        }
    ],
    "provider": {"organization": "", "url": ""},
    "version": "1.0.0",
    "capabilities": {
        "streaming": True,
        "pushNotifications": False,
        "extendedAgentCard": True,
    },
    "securitySchemes": {
        "bearer": {
            "httpAuthSecurityScheme": {"scheme": "bearer", "bearerFormat": "JWT"}
        }
    },
    "securityRequirements": [{"schemes": {"bearer": {"list": []}}}],
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain"],
    "skills": [
        {
            "id": "conversation",
            "name": "Conversation",
            "description": "General conversation ability",
            "tags": [],
        }
    ],
}

CARD_PATH = "/v1/a2a/assistants/a1/.well-known/agent-card.json"


def _http_error(status, body):
    response = requests.Response()
    response.status_code = status
    response._content = requests.compat.json.dumps(body).encode()
    return HTTPError(response=response)


class FakeApi:
    def __init__(self, result):
        self._result = result
        self.calls = []

    def get(self, endpoint, response_model, wrap_response=True):
        self.calls.append(endpoint)
        if isinstance(self._result, Exception):
            raise self._result
        return response_model.model_validate(self._result)


def _service(result):
    service = A2AService("https://api.example.com", "token")
    service._api = FakeApi(result)
    return service


def test_parses_v1_card():
    card = AgentCard.model_validate(V1_CARD)

    assert card.protocol_version == "1.0"
    assert card.supportedInterfaces[0].protocolBinding == "JSONRPC"
    assert card.capabilities.extendedAgentCard is True
    assert "bearer" in card.securitySchemes


def test_get_agent_card_uses_v1_path():
    service = _service(V1_CARD)

    card = service.get_agent_card("a1")

    assert card.protocol_version == "1.0"
    assert service._api.calls == [CARD_PATH]


@pytest.mark.parametrize("status", [403, 404])
def test_get_agent_card_propagates_errors(status):
    service = _service(_http_error(status, {"detail": "error"}))

    with pytest.raises(HTTPError) as exc_info:
        service.get_agent_card("a1")

    assert exc_info.value.response.status_code == status
    assert service._api.calls == [CARD_PATH]
