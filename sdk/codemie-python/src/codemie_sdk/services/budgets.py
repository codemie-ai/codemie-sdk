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

"""Budgets service for the CodeMie SDK (administration of global budgets)."""

import requests

from ..utils import ApiRequestHandler, TokenSource


class BudgetsService:
    """Service for the administration routes of global budgets under ``/v1/admin/budgets``."""

    def __init__(self, api_domain: str, token: TokenSource, verify_ssl: bool = True):
        """Initialize the budgets service.

        Args:
            api_domain: Base URL for the CodeMie API
            token: Authentication token
            verify_ssl: Whether to verify SSL certificates
        """
        self._api = ApiRequestHandler(api_domain, token, verify_ssl)

    def delete(self, budget_id: str) -> requests.Response:
        """Delete a manually created global budget (maintainer only).

        The server answers 204 No Content on success. The raw response is returned so the
        caller can read the status. A budget with assigned users (409), a preconfigured
        budget (403), an unknown or non-global budget id (404), a caller who is not a
        maintainer (403) and a provider failure (502) raise ``requests.HTTPError``; the
        status and message are on ``exc.response``.

        Args:
            budget_id: The budget identifier

        Returns:
            The raw HTTP response (status 204, empty body).
        """
        if not budget_id:
            raise ValueError("budget_id must be a non-empty string")
        return self._api.request(
            "DELETE",
            f"/v1/admin/budgets/{budget_id}",
            requests.Response,
        )
