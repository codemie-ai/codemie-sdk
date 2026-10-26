"""A2A (agent-to-agent) service implementation."""

from requests import HTTPError

from ..models.a2a import AgentCard
from ..utils import ApiRequestHandler, TokenSource

AGENT_CARD_PATH = "/v1/a2a/assistants/{assistant_id}/.well-known/agent-card.json"
LEGACY_AGENT_CARD_PATH = "/v1/a2a/assistants/{assistant_id}/.well-known/agent.json"


def _is_route_not_found(error: HTTPError) -> bool:
    # A missing assistant also returns 404, but with a specific detail message;
    # only the framework's bare "Not Found" means the route itself is absent.
    response = error.response
    if response is None or response.status_code != 404:
        return False
    try:
        return response.json().get("detail") == "Not Found"
    except ValueError:
        return False


class A2AService:
    """Service for A2A agent discovery endpoints."""

    def __init__(self, api_domain: str, token: TokenSource, verify_ssl: bool = True):
        """Initialize the A2A service.

        Args:
            api_domain: Base URL for the CodeMie API
            token: Authentication token
            verify_ssl: Whether to verify SSL certificates
        """
        self._api = ApiRequestHandler(api_domain, token, verify_ssl)

    def get_agent_card(self, assistant_id: str) -> AgentCard:
        """Get the A2A agent card for an assistant.

        Uses the A2A v1.0 well-known path and falls back to the legacy
        ``agent.json`` path on backends that predate the protocol upgrade.

        Args:
            assistant_id: ID of the assistant

        Returns:
            AgentCard: agent discovery metadata for the assistant
        """
        try:
            return self._api.get(
                AGENT_CARD_PATH.format(assistant_id=assistant_id),
                AgentCard,
                wrap_response=False,
            )
        except HTTPError as error:
            if not _is_route_not_found(error):
                raise
        return self._api.get(
            LEGACY_AGENT_CARD_PATH.format(assistant_id=assistant_id),
            AgentCard,
            wrap_response=False,
        )
