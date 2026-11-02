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

"""Unit tests for the Usage Attribution analytics service."""

from unittest.mock import MagicMock, patch

import pytest

from codemie_sdk.models.usage_attribution import (
    UsageAttributionQueryParams,
    UsageAttributionResponse,
    UsageAttributionSettingsResponse,
    UsageAttributionTableResponse,
)
from codemie_sdk.services.usage_attribution import UsageAttributionService

_BASE = "https://api.example.com/v1/analytics/usage-attribution"
_RANGE = {
    "from": "2026-09-01T00:00:00Z",
    "to": "2026-10-01T00:00:00Z",
    "days": 30.0,
    "clamped": False,
    "requested_from": "2026-09-01T00:00:00Z",
    "requested_to": "2026-10-01T00:00:00Z",
    "evidence_from": "2026-09-01T00:00:00Z",
}
_ANALYSIS = {
    "computed_at": "2026-10-01T00:00:00Z",
    "duration_ms": 12.5,
    "cache": "hit",
    "settings": {"hash": "h", "defaults_hash": "d", "schema_version": 1},
}
_VIEW = {"data": {"total": 1.5}, "range": _RANGE, "analysis": None}
_TABLE = {
    "data": {"rows": [{"name": "p"}], "totals": {}},
    "pagination": {"page": 0, "per_page": 10, "total_count": 1, "has_more": False},
    "counts": {"threshold": 1, "all": 1},
    "threshold": 1000.0,
    "display": {"scale": 1.0},
    "range": _RANGE,
    "analysis": _ANALYSIS,
}


def _ok_response(body: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.content = b"{}"
    response.json.return_value = body
    return response


@pytest.fixture
def service() -> UsageAttributionService:
    return UsageAttributionService("https://api.example.com", "token")


def test_get_totals_calls_totals_route_with_period(service):
    params = UsageAttributionQueryParams(time_period="last_7_days")

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(_VIEW)
        result = service.get_totals(params)

    assert get.call_args.kwargs["url"] == f"{_BASE}/totals"
    assert get.call_args.kwargs["params"] == {"time_period": "last_7_days"}
    assert get.call_args.kwargs["headers"]["Authorization"] == "Bearer token"
    assert isinstance(result, UsageAttributionResponse)
    assert result.data == {"total": 1.5}
    assert result.analysis is None
    assert result.range.from_ == "2026-09-01T00:00:00Z"
    assert result.range.clamped is False


def test_get_totals_sends_no_params_by_default(service):
    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(_VIEW)
        service.get_totals()

    assert get.call_args.kwargs["params"] == {}


def test_get_totals_sends_custom_dates(service):
    params = UsageAttributionQueryParams(
        start_date="2026-09-01T00:00:00Z", end_date="2026-10-01T00:00:00Z"
    )

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(_VIEW)
        service.get_totals(params)

    assert get.call_args.kwargs["params"] == {
        "start_date": "2026-09-01T00:00:00Z",
        "end_date": "2026-10-01T00:00:00Z",
    }


@pytest.mark.parametrize(
    "method, path",
    [("get_status", "/status"), ("get_cli_summary", "/cli-summary")],
)
def test_analysis_views_parse_analysis_block(service, method, path):
    body = {**_VIEW, "analysis": _ANALYSIS}

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(body)
        result = getattr(service, method)()

    assert get.call_args.kwargs["url"] == f"{_BASE}{path}"
    assert result.analysis.computed_at == "2026-10-01T00:00:00Z"
    assert result.analysis.cache == "hit"
    assert result.analysis.stale is False
    assert result.analysis.settings.hash == "h"


def test_get_settings_returns_settings_payload(service):
    body = {"data": {"can_tune": True, "settings": []}}

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(body)
        result = service.get_settings()

    assert get.call_args.kwargs["url"] == f"{_BASE}/settings"
    assert isinstance(result, UsageAttributionSettingsResponse)
    assert result.data["can_tune"] is True


@pytest.mark.parametrize(
    "method, kwargs, path",
    [
        ("get_shared_projects", {"scope": "all"}, "/shared-projects"),
        ("get_repository_groups", {"scope": "all"}, "/repository-groups"),
        ("get_people", {"filter": "cand"}, "/people"),
    ],
)
def test_lists_send_paging_search_and_scope(service, method, kwargs, path):
    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(_TABLE)
        result = getattr(service, method)(
            search="abc", page=1, per_page=5, sort_by="ncb", sort_order="asc", **kwargs
        )

    assert get.call_args.kwargs["url"] == f"{_BASE}{path}"
    assert get.call_args.kwargs["params"] == {
        "search": "abc",
        "page": 1,
        "per_page": 5,
        "sort_by": "ncb",
        "sort_order": "asc",
        **kwargs,
    }
    assert isinstance(result, UsageAttributionTableResponse)
    assert result.pagination.total_count == 1
    assert result.counts == {"threshold": 1, "all": 1}
    assert result.data["rows"] == [{"name": "p"}]


def test_lists_leave_unset_options_to_the_server(service):
    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(_TABLE)
        service.get_shared_projects(
            UsageAttributionQueryParams(time_period="last_30_days")
        )

    assert get.call_args.kwargs["params"] == {"time_period": "last_30_days"}


@pytest.mark.parametrize(
    "method, entity, expected_path",
    [
        ("get_shared_project", "My Project/x", "/shared-projects/My%20Project%2Fx"),
        ("get_repository_group", "g-abc123", "/repository-groups/g-abc123"),
        ("get_person", "user@example.com", "/people/user%40example.com"),
    ],
)
def test_popups_quote_the_entity_in_the_path(service, method, entity, expected_path):
    body = {"data": {"row": {}, "detail": {}}, "range": _RANGE, "analysis": _ANALYSIS}

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(body)
        result = getattr(service, method)(entity)

    assert get.call_args.kwargs["url"] == f"{_BASE}{expected_path}"
    assert result.data == {"row": {}, "detail": {}}


def test_get_breakdown_sends_dimension_and_category(service):
    body = {"data": {"rows": [], "total": 0.0}, "range": _RANGE, "analysis": _ANALYSIS}

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(body)
        result = service.get_breakdown(dimension="job", category="pet_project")

    assert get.call_args.kwargs["url"] == f"{_BASE}/breakdown"
    assert get.call_args.kwargs["params"] == {
        "dimension": "job",
        "category": "pet_project",
    }
    assert result.data["total"] == 0.0


def test_range_reports_clamping_fields(service):
    clamped = {
        **_RANGE,
        "days": 90.0,
        "clamped": True,
        "requested_from": "2026-06-01T00:00:00Z",
    }

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response({**_VIEW, "range": clamped})
        result = service.get_totals()

    assert result.range.clamped is True
    assert result.range.days == 90.0
    assert result.range.requested_from == "2026-06-01T00:00:00Z"


def test_client_exposes_usage_attribution_service():
    from codemie_sdk import CodeMieClient

    client = CodeMieClient(
        auth_server_url="",
        auth_realm_name="",
        codemie_api_domain="http://localhost:8080",
    )

    assert isinstance(client.usage_attribution, UsageAttributionService)
