"""Toolkit-management policy service.

Wraps:
  GET /v1/config                      - used to read the features:toolkitManagement flag
  GET /v1/toolkit-management/policy   - read the approved toolkits (admin/maintainer)
  PUT /v1/toolkit-management/policy   - replace the approved toolkits (admin/maintainer)
"""

from ..models.toolkit_policy import ApprovedToolkit, ToolkitPolicy
from ..utils.http import ApiRequestHandler, TokenSource
from .customer_config_service import CustomerConfigService

TOOLKIT_MANAGEMENT_COMPONENT_ID = "features:toolkitManagement"
POLICY_ENDPOINT = "/v1/toolkit-management/policy"


class ToolkitPolicyService:
    """Service for reading and setting the toolkit-management policy."""

    def __init__(self, api_domain: str, token: TokenSource, verify_ssl: bool = True):
        """Initialize the toolkit policy service.

        Args:
            api_domain: Base URL for the CodeMie API
            token: Authentication token source
            verify_ssl: Whether to verify SSL certificates. Default: True
        """
        self._api = ApiRequestHandler(api_domain, token, verify_ssl)
        self._config = CustomerConfigService(api_domain, token, verify_ssl)

    def _flag_enabled(self) -> bool:
        # The flag is ON only when the component is present in GET /v1/config
        # with settings.enabled true; a present-but-disabled entry means OFF.
        return any(
            c.get("id") == TOOLKIT_MANAGEMENT_COMPONENT_ID
            and (c.get("settings") or {}).get("enabled") is True
            for c in self._config.get_config()
        )

    @staticmethod
    def _to_policy(data) -> ToolkitPolicy:
        raw = data.get("approved_toolkits") if isinstance(data, dict) else data
        toolkits = [ApprovedToolkit.model_validate(t) for t in (raw or [])]
        return ToolkitPolicy(
            flag_enabled=True,
            in_effect=bool(toolkits),
            approved_toolkits=toolkits,
        )

    def get_policy(self) -> ToolkitPolicy:
        """Read the toolkit policy.

        When the feature flag is off the admin-only policy endpoint is not
        called and ``flag_enabled=False, in_effect=False, approved_toolkits=None``
        is returned.

        Raises:
            requests.HTTPError: On non-2xx from the policy endpoint (e.g. 403).
        """
        if not self._flag_enabled():
            return ToolkitPolicy(
                flag_enabled=False, in_effect=False, approved_toolkits=None
            )
        data = self._api.get(POLICY_ENDPOINT, dict, wrap_response=False)
        return self._to_policy(data)

    def set_policy(self, approved_toolkits: list[ApprovedToolkit]) -> ToolkitPolicy:
        """Replace the whole policy (PUT, full replacement).

        ``tools=None`` is sent as ``null``; an empty list sends
        ``{"approved_toolkits": []}``.

        Raises:
            requests.HTTPError: 400 on validation failure, 403 for non-admins.
        """
        body = {
            "approved_toolkits": [
                {"toolkit": t.toolkit, "tools": t.tools} for t in approved_toolkits
            ]
        }
        data = self._api.put(POLICY_ENDPOINT, dict, json_data=body, wrap_response=False)
        return self._to_policy(data)