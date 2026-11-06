# Copyright 2026 EPAM Systems, Inc. ("EPAM")
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Provisioning service for the CodeMie SDK.

Wraps the third-party provisioning routes under ``/v1/provisioning``. Only registered
provisioning clients may call them, each with its own bearer token; any other caller,
including an admin, is rejected with HTTP 403.
"""

from urllib.parse import quote

import requests

from ..models.provisioning import (
    ProvisioningBudgetRequest,
    ProvisioningBudgetResponse,
    ProvisioningBudgetResult,
    ProvisioningProject,
)
from ..utils.http import ApiRequestHandler, TokenSource

_PROJECTS_URL = "/v1/provisioning/projects"
_CHANGE_REFERENCE_HEADER = "X-Change-Reference"


class ProvisioningService:
    """Service for the provisioning routes: member project lookup and project budgets.

    A registered client authenticates with its own token, not the token of the user the
    :class:`CodeMieClient` was created for. Build a service for a client with
    :meth:`with_token`, or construct one directly.
    """

    def __init__(self, api_domain: str, token: TokenSource, verify_ssl: bool = True):
        """Initialize the ProvisioningService.

        Args:
            api_domain: Base URL for the CodeMie API
            token: Authentication token of the caller (a provisioning client's token for
                the calls to succeed)
            verify_ssl: Whether to verify SSL certificates
        """
        self._api_domain = api_domain.rstrip("/")
        self._token = token
        self._verify_ssl = verify_ssl
        self._api = ApiRequestHandler(self._api_domain, token, verify_ssl)

    def with_token(self, token: TokenSource) -> "ProvisioningService":
        """Return a service for the same API that authenticates with another token.

        Args:
            token: Authentication token, for example the token of a provisioning client

        Returns:
            A new ProvisioningService; this one is left unchanged
        """
        return ProvisioningService(self._api_domain, token, self._verify_ssl)

    def list_projects(self, member_emails: list[str]) -> list[ProvisioningProject]:
        """List the shared projects that any of the given people belong to.

        The result is the distinct union across all emails, sorted by project name,
        without personal projects. Emails with no active user are skipped, and an empty
        list is returned when none match. The emails are sent as given; the server
        rejects an empty list or an invalid email with HTTP 422.

        Args:
            member_emails: Emails of the people whose projects to list

        Returns:
            List of ProvisioningProject with the project name and display name

        Raises:
            HTTPError: If the request fails, for example 403 when the caller is not a
                client holding the read-projects permission
        """
        return self._api.get(
            _PROJECTS_URL,
            response_model=list[ProvisioningProject],
            params={"member_email": member_emails},
            wrap_response=False,
        )

    def set_budget(
        self,
        project_name: str,
        change_reference: str | None,
        request: ProvisioningBudgetRequest,
    ) -> ProvisioningBudgetResult:
        """Replace the amounts of a project budget, creating the project and budget if missing.

        A category left out of ``request.amounts`` gets 0 and ``platform`` must be above 0.
        The answer is 201 when the call created the budget and 200 when it replaced one.

        Args:
            project_name: CodeMie project name, sent as given
            change_reference: The caller's reference for this change, sent as the
                ``X-Change-Reference`` header; ``None`` leaves the header out so the
                server's rejection of a missing reference can be observed
            request: Amounts and optional project block

        Returns:
            ProvisioningBudgetResult with the HTTP status and the budget after the call

        Raises:
            HTTPError: If the request is rejected (400, 403, 409, 422) or fails (500, 502)
        """
        return self._send_budget("PUT", project_name, change_reference, request)

    def adjust_budget(
        self,
        project_name: str,
        change_reference: str | None,
        request: ProvisioningBudgetRequest,
    ) -> ProvisioningBudgetResult:
        """Merge amounts into a project budget: a listed category changes, 0 removes it.

        A category left out of ``request.amounts`` keeps its amount. The answer is
        always 200 on success.

        Args:
            project_name: CodeMie project name, sent as given
            change_reference: The caller's reference for this change; ``None`` leaves
                the ``X-Change-Reference`` header out
            request: Amounts and optional project block

        Returns:
            ProvisioningBudgetResult with the HTTP status and the budget after the call

        Raises:
            HTTPError: If the request is rejected (400, 403, 409, 422) or fails (500, 502)
        """
        return self._send_budget("PATCH", project_name, change_reference, request)

    def cancel_budget(
        self, project_name: str, change_reference: str | None
    ) -> ProvisioningBudgetResult:
        """Delete a project budget. A project without a budget is not an error.

        Args:
            project_name: CodeMie project name, sent as given
            change_reference: The caller's reference for this change; ``None`` leaves
                the ``X-Change-Reference`` header out

        Returns:
            ProvisioningBudgetResult with status 204 and no body

        Raises:
            HTTPError: If the request is rejected (403, 404, 409, 422) or fails (500)
        """
        return self._send_budget("DELETE", project_name, change_reference, None)

    def _send_budget(
        self,
        method: str,
        project_name: str,
        change_reference: str | None,
        request: ProvisioningBudgetRequest | None,
    ) -> ProvisioningBudgetResult:
        """Send a budget call and return the status with the parsed body.

        The shared request handler parses the body and drops the status, and 201 versus
        200 is part of the set contract, so these routes are sent directly.
        """
        token = self._token() if callable(self._token) else self._token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        if change_reference is not None:
            headers[_CHANGE_REFERENCE_HEADER] = change_reference

        response = requests.request(
            method,
            f"{self._api_domain}{_PROJECTS_URL}/{quote(project_name, safe='')}/budget",
            headers=headers,
            data=(
                request.model_dump_json(exclude_none=True)
                if request is not None
                else None
            ),
            verify=self._verify_ssl,
        )
        response.raise_for_status()

        if response.status_code == 204 or not response.content:
            return ProvisioningBudgetResult(status_code=response.status_code)
        return ProvisioningBudgetResult(
            status_code=response.status_code,
            budget=ProvisioningBudgetResponse.model_validate(response.json()),
        )
