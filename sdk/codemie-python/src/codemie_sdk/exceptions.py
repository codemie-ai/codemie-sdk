"""Custom exceptions for the CodeMie SDK."""

import requests


class CodeMieError(Exception):
    """Base exception for all CodeMie SDK errors."""

    pass


class ApiError(CodeMieError):
    """Exception raised for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: dict | None = None,
    ):
        """Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code if applicable
            response: Raw API response if available
        """
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class NotFoundError(ApiError):
    """Exception raised when a resource is not found."""

    def __init__(self, resource_type: str, resource_id: str):
        """Initialize not found error.

        Args:
            resource_type: Type of resource that was not found (e.g., "Integration")
            resource_id: ID or identifier of the resource
        """
        super().__init__(
            message=f"{resource_type} with {resource_id} not found", status_code=404
        )


POLICY_LABEL = "toolkit-management policy"


class ToolkitNotApprovedError(requests.HTTPError):
    """Raised when a save is refused because a toolkit or tool is not approved.

    Subclasses ``requests.HTTPError`` so existing ``except requests.HTTPError``
    handlers keep working.
    """

    policy = POLICY_LABEL

    def __init__(
        self,
        message: str,
        toolkit: str | None = None,
        tool: str | None = None,
        response: requests.Response | None = None,
    ):
        """Initialize the error.

        Args:
            message: Verbatim server message
            toolkit: Refused toolkit name
            tool: Refused tool name (None for toolkit-level refusals)
            response: Original HTTP response
        """
        self.message = message
        self.toolkit = toolkit
        self.tool = tool
        self.status_code = response.status_code if response is not None else 400
        target = (
            f"tool '{tool}' in toolkit '{toolkit}'" if tool else f"toolkit '{toolkit}'"
        )
        super().__init__(
            f"{message} ({target}; refused by {self.policy})", response=response
        )