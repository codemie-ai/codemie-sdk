from unittest.mock import MagicMock, patch

from codemie_sdk.models.analytics import (
    AnalyticsQueryParams,
    PaginatedAnalyticsQueryParams,
    SummariesResponse,
    TabularResponse,
)
from codemie_sdk.services.analytics import AnalyticsService

_META = {
    "timestamp": "2026-01-01T00:00:00Z",
    "data_as_of": "2026-01-01T00:00:00Z",
    "filters_applied": {},
    "execution_time_ms": 1.0,
}
_SUMMARY_BODY = {
    "data": {
        "metrics": [
            {
                "id": "tokens_saved",
                "label": "Tokens saved",
                "type": "number",
                "value": 42,
            }
        ]
    },
    "metadata": _META,
}
_TABULAR_BODY = {
    "data": {
        "columns": [{"id": "strategy", "label": "Strategy", "type": "string"}],
        "rows": [{"strategy": "balanced", "tokens_saved": 10}],
    },
    "metadata": _META,
    "pagination": {"page": 0, "per_page": 20, "total_count": 1, "has_more": False},
}
_BASE = "https://api.example.com"


def _ok_response(body: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = body
    return response


def _service() -> AnalyticsService:
    return AnalyticsService(_BASE, "token")


def _call(method_name, body, *args):
    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(body)
        result = getattr(_service(), method_name)(*args)
    return result, get.call_args.kwargs


FILTERS = {
    "users": "u1,u2",
    "projects": "p1",
    "start_date": "2026-01-01T00:00:00Z",
    "end_date": "2026-01-02T00:00:00Z",
}


def test_headroom_summary_hits_url_and_parses_response():
    result, kwargs = _call(
        "get_headroom_summary",
        _SUMMARY_BODY,
        AnalyticsQueryParams(time_period="last_7_days"),
    )
    assert isinstance(result, SummariesResponse)
    assert kwargs["url"] == f"{_BASE}/v1/analytics/headroom/summary"
    assert kwargs["params"] == {"time_period": "last_7_days"}


def test_headroom_summary_sends_only_declared_filters():
    _, kwargs = _call(
        "get_headroom_summary", _SUMMARY_BODY, AnalyticsQueryParams(**FILTERS)
    )
    assert kwargs["params"] == FILTERS


def test_headroom_summary_without_params_sends_no_query():
    _, kwargs = _call("get_headroom_summary", _SUMMARY_BODY)
    assert kwargs["params"] == {}


def test_headroom_timeseries_hits_url_and_parses_response():
    result, kwargs = _call(
        "get_headroom_timeseries", _TABULAR_BODY, AnalyticsQueryParams(**FILTERS)
    )
    assert isinstance(result, TabularResponse)
    assert kwargs["url"] == f"{_BASE}/v1/analytics/headroom/timeseries"
    assert kwargs["params"] == FILTERS


def test_headroom_timeseries_without_params_sends_no_query():
    _, kwargs = _call("get_headroom_timeseries", _TABULAR_BODY)
    assert kwargs["params"] == {}


def test_headroom_by_strategy_sends_pagination_and_filters():
    result, kwargs = _call(
        "get_headroom_by_strategy",
        _TABULAR_BODY,
        PaginatedAnalyticsQueryParams(page=2, per_page=5, **FILTERS),
    )
    assert isinstance(result, TabularResponse)
    assert result.pagination.total_count == 1
    assert kwargs["url"] == f"{_BASE}/v1/analytics/headroom/by-strategy"
    assert kwargs["params"] == {"page": 2, "per_page": 5, **FILTERS}


def test_headroom_by_strategy_without_params_sends_no_query():
    _, kwargs = _call("get_headroom_by_strategy", _TABULAR_BODY)
    assert kwargs["params"] == {}
