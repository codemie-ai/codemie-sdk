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

"""Scheduler service for the CodeMie SDK."""

from ..models.scheduler import SchedulerListResponse
from ..utils import ApiRequestHandler, TokenSource


class SchedulerService:
    """Service for reading CodeMie schedulers."""

    def __init__(self, api_domain: str, token: TokenSource, verify_ssl: bool = True):
        """Initialize the scheduler service.

        Args:
            api_domain: Base URL for the CodeMie API
            token: Authentication token
            verify_ssl: Whether to verify SSL certificates
        """
        self._api = ApiRequestHandler(api_domain, token, verify_ssl)

    def list(
        self,
        page: int = 0,
        per_page: int = 10,
        owner_type: str | None = None,
    ) -> SchedulerListResponse:
        """List the schedulers visible to the caller.

        Calls ``GET /v1/schedulers``. The page size is sent as ``pageSize`` and the
        owner filter as ``ownerType``, the names the API defines.

        Args:
            page: Page number (0-indexed)
            per_page: Items per page (1 to 100)
            owner_type: Optional owner filter, ``"user"`` or ``"project"``. ``None``
                omits the parameter, which is the API's default listing.

        Returns:
            SchedulerListResponse with the scheduler rows and pagination info

        Raises:
            HTTPError: If the request fails
        """
        params: dict[str, str | int] = {"page": page, "pageSize": per_page}
        if owner_type is not None:
            params["ownerType"] = owner_type

        return self._api.get(
            "/v1/schedulers",
            SchedulerListResponse,
            params=params,
            wrap_response=False,
        )
