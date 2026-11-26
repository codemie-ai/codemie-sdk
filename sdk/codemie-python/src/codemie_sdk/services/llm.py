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

    def list_for_project(
        self, project_id: str, include_all: bool = False
    ) -> list[LLMModel]:
        """Get the LLM models available to the caller in a project.

        The list follows the project's model settings and the caller's own model
        override in that project; the model flagged ``default`` is the override's
        default, else the project's default, else the platform default.

        Args:
            project_id: Name of the project to list the models for
            include_all: Whether to include all models, not only the default set.
                Default: False

        Returns:
            List of LLM models

        Raises:
            HTTPError: 403 when the caller has no access to the project, 404 when the
                project is unknown
        """
        params = {"project_id": project_id}
        if include_all:
            params["include_all"] = "true"
        return self._api.get(
            "/v1/llm_models",
            list[LLMModel],
            params=params,
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
