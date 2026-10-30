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

"""Marketplace management service for the CodeMie SDK.

Wraps the assistant review queue under ``/v1/marketplace-management``. Every route
requires the admin or maintainer role.
"""

from enum import Enum
from typing import Any
from urllib.parse import quote

from ..models.marketplace_management import (
    MarketplaceAssistantsResponse,
    MarketplaceDecisionRequest,
    MarketplaceForcePublishResponse,
    MarketplaceGateResult,
    MarketplaceOverview,
    MarketplacePendingOrderBy,
    MarketplacePendingResponse,
    MarketplaceReviewActionResponse,
    MarketplaceReviewDetail,
    MarketplaceStatusFilter,
)
from ..utils import ApiRequestHandler, TokenSource

_BASE = "/v1/marketplace-management/entities/assistants"
_IDEMPOTENCY_HEADER = "Idempotency-Key"


def _value(item: Any) -> Any:
    """The wire value of an enum member; other values pass through."""
    return item.value if isinstance(item, Enum) else item


class MarketplaceManagementService:
    """Service for reviewing assistants submitted to the marketplace."""

    def __init__(self, api_domain: str, token: TokenSource, verify_ssl: bool = True):
        """Initialize the marketplace management service.

        Args:
            api_domain: Base URL for the CodeMie API
            token: Authentication token
            verify_ssl: Whether to verify SSL certificates
        """
        self._api = ApiRequestHandler(api_domain, token, verify_ssl)

    @staticmethod
    def _path(*parts: str) -> str:
        return "/".join([_BASE, *(quote(part, safe="") for part in parts)])

    def get_overview(self) -> MarketplaceOverview:
        """Marketplace health figures, including the size of the review queue."""
        return self._api.get(
            f"{_BASE}/overview", MarketplaceOverview, wrap_response=False
        )

    def list_pending(
        self,
        category: str | None = None,
        gate_result: MarketplaceGateResult | str | None = None,
        order_by: MarketplacePendingOrderBy | str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> MarketplacePendingResponse:
        """List the assistants waiting for review.

        Args:
            category: Only assistants in this category id
            gate_result: Only assistants with this live gate result
            order_by: Sort order; the server default is oldest submission first
            page: Page number, starting at 1
            page_size: Page size, 1 to 100
        """
        params = {
            "category": category,
            "gate_result": _value(gate_result),
            "order_by": _value(order_by),
            "page": page,
            "page_size": page_size,
        }
        return self._api.get(
            f"{_BASE}/pending",
            MarketplacePendingResponse,
            params={key: value for key, value in params.items() if value is not None},
            wrap_response=False,
        )

    def list_marketplace_assistants(
        self,
        status: MarketplaceStatusFilter | str | None = None,
        page: int = 1,
        page_size: int | None = None,
    ) -> MarketplaceAssistantsResponse:
        """List assistants by review status.

        Args:
            status: Status filter; the server default is all statuses
            page: Page number, starting at 1
            page_size: Page size, 1 to 100; omit to get every matching row
        """
        params = {"status": _value(status), "page": page, "page_size": page_size}
        return self._api.get(
            f"{_BASE}/marketplace-assistants",
            MarketplaceAssistantsResponse,
            params={key: value for key, value in params.items() if value is not None},
            wrap_response=False,
        )

    def get_detail(self, entity_id: str) -> MarketplaceReviewDetail:
        """Review detail of one assistant, with its gate findings recomputed live."""
        return self._api.get(
            self._path(entity_id), MarketplaceReviewDetail, wrap_response=False
        )

    def _decide(
        self,
        entity_id: str,
        action: str,
        request: MarketplaceDecisionRequest,
        response_model: type,
        idempotency_key: str | None = None,
    ):
        return self._api.post(
            f"{self._path('pending', entity_id)}/{action}",
            response_model,
            json_data=request.to_body(),
            extra_headers=(
                {_IDEMPOTENCY_HEADER: idempotency_key} if idempotency_key else None
            ),
            wrap_response=False,
        )

    def approve(
        self,
        entity_id: str,
        expected_version: int | None = None,
        idempotency_key: str | None = None,
    ) -> MarketplaceReviewActionResponse:
        """Approve a pending assistant: publish and verify it.

        Args:
            entity_id: Assistant ID
            expected_version: marketplace_version the reviewer looked at; a different
                current version is refused with HTTP 409
            idempotency_key: Replay token; the same key returns the first answer
        """
        return self._decide(
            entity_id,
            "approve",
            MarketplaceDecisionRequest(expected_version=expected_version),
            MarketplaceReviewActionResponse,
            idempotency_key,
        )

    def reject(
        self,
        entity_id: str,
        reason: str,
        expected_version: int | None = None,
    ) -> MarketplaceReviewActionResponse:
        """Reject a pending assistant: unpublish and unverify it.

        Args:
            entity_id: Assistant ID
            reason: 20 to 2000 characters after trimming, kept with the assistant
            expected_version: marketplace_version the reviewer looked at
        """
        return self._decide(
            entity_id,
            "reject",
            MarketplaceDecisionRequest(
                reason=reason, expected_version=expected_version
            ),
            MarketplaceReviewActionResponse,
        )

    def force_publish(
        self,
        entity_id: str,
        override_notice: str,
        expected_version: int | None = None,
    ) -> MarketplaceForcePublishResponse:
        """Publish an assistant over its CRITICAL gate findings.

        Args:
            entity_id: Assistant ID
            override_notice: 20 to 2000 characters after trimming, recorded with the decision
            expected_version: marketplace_version the reviewer looked at
        """
        return self._decide(
            entity_id,
            "force-publish",
            MarketplaceDecisionRequest(
                override_notice=override_notice, expected_version=expected_version
            ),
            MarketplaceForcePublishResponse,
        )

    def withdraw(
        self, entity_id: str, expected_version: int | None = None
    ) -> MarketplaceReviewActionResponse:
        """Withdraw an assistant from the marketplace: unpublish and unverify it.

        Args:
            entity_id: Assistant ID
            expected_version: marketplace_version the caller looked at. The route reads
                no body fields today, so the server accepts and ignores it.
        """
        return self._decide(
            entity_id,
            "withdraw",
            MarketplaceDecisionRequest(expected_version=expected_version),
            MarketplaceReviewActionResponse,
        )
