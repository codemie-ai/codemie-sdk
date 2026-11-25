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

"""Unit tests for the marketplace management service and the assistant review fields."""

from unittest.mock import MagicMock, patch

import pytest
import requests
from pydantic import ValidationError

from codemie_sdk.client.client import CodeMieClient
from codemie_sdk.models.assistant import Assistant
from codemie_sdk.models.marketplace_management import (
    MarketplaceAssistantsResponse,
    MarketplaceAuditRunStatus,
    MarketplaceAuditStatus,
    MarketplaceCleanupBucket,
    MarketplaceCleanupOrderBy,
    MarketplaceCleanupReason,
    MarketplaceCleanupResponse,
    MarketplaceCleanupRow,
    MarketplaceGateRule,
    MarketplaceForcePublishResponse,
    MarketplaceGateResult,
    MarketplaceOverview,
    MarketplacePendingOrderBy,
    MarketplacePendingResponse,
    MarketplaceReviewActionResponse,
    MarketplaceReviewDetail,
    MarketplaceSimilarPair,
    MarketplaceStatusFilter,
    MarketplaceUsageTier,
    MarketplaceVerdictKind,
)
from codemie_sdk.services.assistant import AssistantService
from codemie_sdk.services.marketplace_management import MarketplaceManagementService

_BASE = "https://api.example.com/v1/marketplace-management/entities/assistants"
_FINDING = {
    "rule": "description_length",
    "severity": "CRITICAL",
    "message": "Description is 5 chars, minimum is 100.",
}
_ACTION = {
    "ok": True,
    "entity_kind": "ASSISTANT",
    "entity_id": "a-1",
    "status": "APPROVED",
    "indexing": {"action": "index", "state": "OK", "attempts": 1, "error": None},
}


def _ok_response(body: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.content = b"{}"
    response.json.return_value = body
    return response


@pytest.fixture
def service() -> MarketplaceManagementService:
    return MarketplaceManagementService("https://api.example.com", "token")


def test_get_overview_parses_pending_block(service):
    body = {
        "total": 12,
        "marketplace_assistants_total": 9,
        "buckets": {"VERIFIED": 3},
        "pending": {"count": 4, "waiting_over_7d": 1, "avg_wait_days": 2.5},
    }

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(body)
        result = service.get_overview()

    assert get.call_args.kwargs["url"] == f"{_BASE}/overview"
    assert get.call_args.kwargs["headers"]["Authorization"] == "Bearer token"
    assert isinstance(result, MarketplaceOverview)
    assert result.pending.count == 4
    assert result.pending.waiting_over_7d == 1
    assert result.pending.avg_wait_days == 2.5
    assert result.buckets == {"VERIFIED": 3}


def test_list_pending_sends_only_given_filters(service):
    body = {
        "total": 1,
        "page": 2,
        "page_size": 10,
        "items": [
            {
                "assistant_id": "a-1",
                "name": "Demo",
                "marketplace_status": "PENDING_REVIEW",
                "submitted_at": 1787000000.5,
                "submitted_by": "someone",
                "gate_findings": [_FINDING],
                "categories": ["quality-assurance"],
            }
        ],
    }

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(body)
        result = service.list_pending(
            category="quality-assurance",
            gate_result=MarketplaceGateResult.HAS_CRITICAL,
            order_by=MarketplacePendingOrderBy.NAME_ASC,
            page=2,
            page_size=10,
        )

    assert get.call_args.kwargs["url"] == f"{_BASE}/pending"
    assert get.call_args.kwargs["params"] == {
        "category": "quality-assurance",
        "gate_result": "has_critical",
        "order_by": "name_asc",
        "page": 2,
        "page_size": 10,
    }
    assert isinstance(result, MarketplacePendingResponse)
    row = result.items[0]
    assert row.assistant_id == "a-1"
    assert row.submitted_at == 1787000000.5
    assert row.gate_findings[0].rule == "description_length"
    assert row.gate_recompute_failed is False


def test_list_pending_defaults_send_paging_only(service):
    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(
            {"total": 0, "page": 1, "page_size": 25, "items": []}
        )
        service.list_pending()

    assert get.call_args.kwargs["params"] == {"page": 1, "page_size": 25}


@pytest.mark.parametrize(
    "status, expected",
    [(MarketplaceStatusFilter.VERIFIED, "VERIFIED"), ("PENDING", "PENDING")],
)
def test_list_marketplace_assistants_sends_status(service, status, expected):
    body = {
        "total": 1,
        "page": 1,
        "page_size": 1,
        "items": [
            {
                "assistant_id": "a-1",
                "is_verified": True,
                "marketplace_decision_reason": None,
            }
        ],
    }

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(body)
        result = service.list_marketplace_assistants(status=status)

    assert get.call_args.kwargs["url"] == f"{_BASE}/marketplace-assistants"
    assert get.call_args.kwargs["params"] == {"status": expected, "page": 1}
    assert isinstance(result, MarketplaceAssistantsResponse)
    assert result.items[0].is_verified is True


def test_get_detail_parses_review_fields(service):
    body = {
        "id": "a-1",
        "name": "Demo",
        "description": "short",
        "marketplace_status": "APPROVED",
        "marketplace_version": 3,
        "is_verified": True,
        "gate_findings": [_FINDING],
        "critical_count": 1,
        "override_notice": "n" * 20,
        "overridden_by": "admin@example.com",
        "bypassed_gate_findings": [_FINDING],
    }

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(body)
        result = service.get_detail("a/1")

    assert get.call_args.kwargs["url"] == f"{_BASE}/a%2F1"
    assert isinstance(result, MarketplaceReviewDetail)
    assert result.marketplace_version == 3
    assert result.gate_findings[0].severity == "CRITICAL"
    assert result.bypassed_gate_findings[0].rule == "description_length"
    assert result.overridden_by == "admin@example.com"


def test_approve_posts_expected_version_and_idempotency_key(service):
    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = _ok_response(_ACTION)
        result = service.approve("a-1", expected_version=2, idempotency_key="key-1")

    assert post.call_args.kwargs["url"] == f"{_BASE}/pending/a-1/approve"
    assert post.call_args.kwargs["json"] == {"expected_version": 2}
    assert post.call_args.kwargs["headers"]["Idempotency-Key"] == "key-1"
    assert isinstance(result, MarketplaceReviewActionResponse)
    assert result.status == "APPROVED"
    assert result.indexing.state == "OK"


def test_approve_without_arguments_sends_empty_body_and_no_key(service):
    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = _ok_response(_ACTION)
        service.approve("a-1")

    assert post.call_args.kwargs["json"] == {}
    assert "Idempotency-Key" not in post.call_args.kwargs["headers"]


def test_reject_posts_reason(service):
    body = {**_ACTION, "status": "REJECTED"}
    reason = "r" * 25

    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = _ok_response(body)
        result = service.reject("a-1", reason, expected_version=1)

    assert post.call_args.kwargs["url"] == f"{_BASE}/pending/a-1/reject"
    assert post.call_args.kwargs["json"] == {"reason": reason, "expected_version": 1}
    assert result.status == "REJECTED"


def test_force_publish_posts_override_notice(service):
    notice = "n" * 25
    body = {
        **_ACTION,
        "override_notice": notice,
        "bypassed_gate_findings": [_FINDING],
    }

    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = _ok_response(body)
        result = service.force_publish("a-1", notice, expected_version=4)

    assert post.call_args.kwargs["url"] == f"{_BASE}/pending/a-1/force-publish"
    assert post.call_args.kwargs["json"] == {
        "override_notice": notice,
        "expected_version": 4,
    }
    assert isinstance(result, MarketplaceForcePublishResponse)
    assert result.override_notice == notice
    assert result.bypassed_gate_findings[0].rule == "description_length"
    assert result.bypassed_gate_findings_unavailable is False


def test_withdraw_posts_to_withdraw_route(service):
    body = {**_ACTION, "status": "WITHDRAWN"}

    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = _ok_response(body)
        result = service.withdraw("a-1", expected_version=5)

    assert post.call_args.kwargs["url"] == f"{_BASE}/pending/a-1/withdraw"
    assert post.call_args.kwargs["json"] == {"expected_version": 5}
    assert result.status == "WITHDRAWN"


def test_http_error_is_raised_for_refused_decision(service):
    response = _ok_response({})
    response.raise_for_status.side_effect = RuntimeError("409 Conflict")

    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = response
        with pytest.raises(RuntimeError, match="409"):
            service.approve("a-1", expected_version=0)


def test_client_exposes_marketplace_management_service():
    with patch("codemie_sdk.client.client.KeycloakCredentials") as credentials:
        credentials.return_value.get_token.return_value = "token"
        client = CodeMieClient(
            auth_server_url="https://auth.example.com",
            auth_realm_name="realm",
            codemie_api_domain="https://api.example.com",
            auth_client_id="id",
            auth_client_secret="secret",
        )

    assert isinstance(client.marketplace_management, MarketplaceManagementService)


def test_assistant_review_fields_default_to_none():
    assistant = Assistant(
        name="Demo", description="d", system_prompt="p", project="demo"
    )

    assert assistant.marketplace_status is None
    assert assistant.is_verified is None
    assert assistant.marketplace_decision_reason is None


def test_assistant_parses_review_fields():
    assistant = Assistant.model_validate(
        {
            "name": "Demo",
            "description": "d",
            "system_prompt": "p",
            "project": "demo",
            "marketplace_status": "REJECTED",
            "is_verified": False,
            "marketplace_decision_reason": "Needs a clearer description.",
        }
    )

    assert assistant.marketplace_status == "REJECTED"
    assert assistant.is_verified is False
    assert assistant.marketplace_decision_reason == "Needs a clearer description."


def test_publish_sends_force_publish_and_override_notice():
    service = AssistantService("https://api.example.com", "token")
    notice = "n" * 25

    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = _ok_response({"message": "ok"})
        service.publish(
            "a-1",
            categories=["quality-assurance"],
            force_publish=True,
            override_notice=notice,
        )

    assert post.call_args.kwargs["url"].endswith(
        "/v1/assistants/a-1/marketplace/publish"
    )
    assert post.call_args.kwargs["json"] == {
        "categories": ["quality-assurance"],
        "force_publish": True,
        "override_notice": notice,
    }


def test_publish_defaults_keep_the_previous_request_body():
    service = AssistantService("https://api.example.com", "token")

    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = _ok_response({"message": "ok"})
        service.publish(
            "a-1", categories=["quality-assurance"], ignore_recommendations=True
        )

    assert post.call_args.kwargs["json"] == {
        "categories": ["quality-assurance"],
        "ignore_recommendations": True,
    }


def test_list_cleanup_sends_only_given_filters(service):
    body = {
        "total": 1,
        "page": 1,
        "page_size": 50,
        "items": [
            {
                "id": "a-1",
                "name": "Demo",
                "creator": "Jane Doe",
                "categories": ["quality-assurance"],
                "bucket": "VERIFIED",
                "critical_count": 0,
                "optional_count": 1,
                "top_similar": None,
            }
        ],
    }

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(body)
        result = service.list_cleanup(bucket=MarketplaceCleanupBucket.ALL, q="Demo")

    assert get.call_args.kwargs["url"] == f"{_BASE}/cleanup"
    assert get.call_args.kwargs["params"] == {
        "bucket": "ALL",
        "q": "Demo",
        "page": 1,
        "page_size": 50,
    }
    assert isinstance(result, MarketplaceCleanupResponse)
    row = result.items[0]
    assert row.creator == "Jane Doe"
    assert row.top_similar is None
    assert "canonical_id" not in row.model_fields_set
    assert "creator" in row.model_fields_set


def test_start_audit_posts_without_body_and_parses_status(service):
    body = {"is_running": True, "run_id": "run-1", "status": "RUNNING", "error": None}
    response = _ok_response(body)
    response.status_code = 202

    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = response
        result = service.start_audit()

    assert post.call_args.kwargs["url"] == f"{_BASE}/audit/run"
    assert post.call_args.kwargs["json"] is None
    assert isinstance(result, MarketplaceAuditStatus)
    assert result.is_running is True
    assert result.run_id == "run-1"


def test_get_audit_status_parses_finished_run(service):
    body = {
        "is_running": False,
        "run_id": "run-1",
        "started_at": 1787000000.0,
        "finished_at": 1787000090.5,
        "error": None,
        "status": "PARTIAL",
        "degraded": True,
        "degraded_reason": "similarity backend unavailable",
    }

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(body)
        result = service.get_audit_status()

    assert get.call_args.kwargs["url"] == f"{_BASE}/audit/status"
    assert result.is_running is False
    assert result.status == "PARTIAL"
    assert result.finished_at == 1787000090.5
    assert result.degraded is True


def test_start_audit_raises_http_error_when_a_run_is_active(service):
    response = _ok_response({"error": "audit_already_running"})
    response.status_code = 409
    response.raise_for_status.side_effect = requests.HTTPError(response=response)

    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = response
        with pytest.raises(requests.HTTPError) as error:
            service.start_audit()

    assert error.value.response.status_code == 409


def test_list_cleanup_sends_every_filter_under_its_server_name(service):
    body = {"total": 0, "page": 3, "page_size": 20, "items": []}

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(body)
        service.list_cleanup(
            bucket=MarketplaceCleanupBucket.DELETE,
            q="demo",
            reason=MarketplaceCleanupReason.DUPLICATE,
            tier=MarketplaceUsageTier.DEAD,
            verdict=MarketplaceVerdictKind.CANDIDATE_FOR_CLEANUP,
            mcp="some-mcp",
            category="quality-assurance",
            cluster_id=7,
            rule=MarketplaceGateRule.NAME_LENGTH,
            order_by=MarketplaceCleanupOrderBy.USERS_ASC,
            page=3,
            page_size=20,
        )

    assert get.call_args.kwargs["params"] == {
        "bucket": "DELETE",
        "q": "demo",
        "reason": "duplicate",
        "tier": "DEAD",
        "verdict": "CANDIDATE_FOR_CLEANUP",
        "mcp": "some-mcp",
        "category": "quality-assurance",
        "cluster_id": 7,
        "rule": "name_length",
        "order_by": "users_asc",
        "page": 3,
        "page_size": 20,
    }


def test_list_cleanup_enum_member_and_plain_string_send_the_same_params(service):
    body = {"total": 0, "page": 1, "page_size": 50, "items": []}

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(body)
        service.list_cleanup(
            bucket=MarketplaceCleanupBucket.ALL,
            tier=MarketplaceUsageTier.HOT,
            order_by=MarketplaceCleanupOrderBy.NAME_ASC,
        )
        with_enums = get.call_args.kwargs["params"]
        service.list_cleanup(bucket="ALL", tier="HOT", order_by="name_asc")
        with_strings = get.call_args.kwargs["params"]

    assert with_enums == with_strings


def test_cleanup_row_parses_known_values_to_enums_and_keeps_unknown_ones():
    known = MarketplaceCleanupRow.model_validate(
        {
            "id": "a-1",
            "usage_tier": "COLD",
            "bucket": "COMMUNITY",
            "verdict_kind": "REVIEW",
            "cleanup_reason": "dead",
            "top_similar": {"a_id": "a-1", "b_id": "a-2", "combined": 0.91},
        }
    )
    unknown = MarketplaceCleanupRow.model_validate(
        {"id": "a-2", "usage_tier": "LUKEWARM", "cleanup_reason": "new_reason"}
    )

    assert known.usage_tier is MarketplaceUsageTier.COLD
    assert known.bucket is MarketplaceCleanupBucket.COMMUNITY
    assert known.verdict_kind is MarketplaceVerdictKind.REVIEW
    assert known.cleanup_reason is MarketplaceCleanupReason.DEAD
    assert isinstance(known.top_similar, MarketplaceSimilarPair)
    assert known.top_similar.combined == 0.91
    assert unknown.usage_tier == "LUKEWARM"
    assert unknown.cleanup_reason == "new_reason"


def test_audit_status_parses_known_status_to_enum_and_keeps_unknown_one():
    known = MarketplaceAuditStatus.model_validate(
        {"is_running": False, "status": "PARTIAL"}
    )
    unknown = MarketplaceAuditStatus.model_validate(
        {"is_running": False, "status": "ARCHIVED"}
    )

    assert known.status is MarketplaceAuditRunStatus.PARTIAL
    assert known.status == "PARTIAL"
    assert unknown.status == "ARCHIVED"


def test_similar_pair_requires_combined_and_keeps_unknown_keys():
    pair = MarketplaceSimilarPair.model_validate(
        {"a_id": "a-1", "b_id": "a-2", "combined": 0.5, "new_key": 1}
    )

    assert pair.signals == {}
    assert pair.model_extra == {"new_key": 1}
    with pytest.raises(ValidationError):
        MarketplaceSimilarPair.model_validate({"a_id": "a-1", "b_id": "a-2"})
