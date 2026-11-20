"""LLM service implementation."""

from __future__ import annotations

from ..models.llm import LLMModel
from ..utils.http import ApiRequestHandler, TokenSource


class LLMService:
    """Service for managing LLM models."""

    def __init__(self, api_domain: str, token: TokenSource, verify_ssl: bool = True):
        """Initialize the LLM models service.

        Args:
            api_domain: Base URL for the CodeMie API
            token: Authentication token
            verify_ssl: Whether to verify SSL certificates. Default: True
        """
        self._api = ApiRequestHandler(api_domain, token, verify_ssl)

    def list(self, include_all: bool = False) -> list[LLMModel]:
        """Get list of available LLM models.

        Args:
            include_all: Whether to include all models, not only the default set.
                Sent as the ``include_all`` query parameter. Default: False

        Returns:
            List of LLM models
        """
        return self._api.get(
            "/v1/llm_models",
            list[LLMModel],
            params={"include_all": "true"} if include_all else None,
            wrap_response=False,
        )

    def list_embeddings(self) -> list[LLMModel]:
        """Get list of available embeddings models.

        Returns:
            List of embeddings models
        """
        return self._api.get(
            "/v1/embeddings_models", list[LLMModel], wrap_response=False
        )
