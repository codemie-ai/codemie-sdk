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

LEGACY_CARD = {
    "name": "assistant",
    "description": "Legacy card",
    "url": "https://api.example.com/v1/a2a/assistants/a1",
    "version": "1.0.0",
    "capabilities": {"streaming": True, "stateTransitionHistory": True},
    "authentication": {"schemes": ["bearer"]},
    "skills": [{"id": "conversation", "name": "Conversation"}],
}


def _http_error(status, body):
    response = requests.Response()
    response.status_code = status
    response._content = requests.compat.json.dumps(body).encode()
    return HTTPError(response=response)


class FakeApi:
    def __init__(self, responses):
        self._responses = dict(responses)
        self.calls = []

    def get(self, endpoint, response_model, wrap_response=True):
        self.calls.append(endpoint)
        result = self._responses[endpoint]
        if isinstance(result, Exception):
            raise result
        return response_model.model_validate(result)


def _service(responses):
    service = A2AService("https://api.example.com", "token")
    service._api = FakeApi(responses)
    return service


NEW = "/v1/a2a/assistants/a1/.well-known/agent-card.json"
OLD = "/v1/a2a/assistants/a1/.well-known/agent.json"


def test_parses_v1_card():
    card = AgentCard.model_validate(V1_CARD)

    assert card.protocol_version == "1.0"
    assert card.supportedInterfaces[0].protocolBinding == "JSONRPC"
    assert card.capabilities.extendedAgentCard is True
    assert "bearer" in card.securitySchemes
    assert card.url is None


def test_parses_legacy_card():
    card = AgentCard.model_validate(LEGACY_CARD)

    assert card.protocol_version is None
    assert card.url == LEGACY_CARD["url"]
    assert card.authentication.schemes == ["bearer"]
    assert card.capabilities.stateTransitionHistory is True


def test_get_agent_card_uses_v1_path():
    service = _service({NEW: V1_CARD})

    card = service.get_agent_card("a1")

    assert card.protocol_version == "1.0"
    assert service._api.calls == [NEW]


def test_get_agent_card_falls_back_when_v1_route_missing():
    service = _service(
        {NEW: _http_error(404, {"detail": "Not Found"}), OLD: LEGACY_CARD}
    )

    card = service.get_agent_card("a1")

    assert card.url == LEGACY_CARD["url"]
    assert service._api.calls == [NEW, OLD]


@pytest.mark.parametrize(
    "status, body",
    [
        (404, {"detail": "Assistant with id a1 wasn't found"}),
        (403, {"detail": "You don't have permission to access this assistant."}),
    ],
)
def test_get_agent_card_does_not_fall_back_on_real_errors(status, body):
    service = _service({NEW: _http_error(status, body), OLD: LEGACY_CARD})

    with pytest.raises(HTTPError) as exc_info:
        service.get_agent_card("a1")

    assert exc_info.value.response.status_code == status
    assert service._api.calls == [NEW]
