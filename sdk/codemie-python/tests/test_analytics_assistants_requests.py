from unittest.mock import MagicMock, patch

from codemie_sdk.models.analytics import (
    PaginatedAnalyticsQueryParams,
    TabularResponse,
)
from codemie_sdk.services.analytics import AnalyticsService

_BODY = {
    "data": {
        "columns": [{"id": "request_id", "label": "Request", "type": "string"}],
        "rows": [{"request_id": "r-1", "assistant_id": "a-1"}],
    },
    "metadata": {
        "timestamp": "2026-01-01T00:00:00Z",
        "data_as_of": "2026-01-01T00:00:00Z",
        "filters_applied": {},
        "execution_time_ms": 1.0,
    },
    "pagination": {"page": 0, "per_page": 20, "total_count": 1, "has_more": False},
}


def _ok_response(body: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = body
    return response


def test_get_assistants_requests_passes_filters_and_parses_rows():
    service = AnalyticsService("https://api.example.com", "token")
    params = PaginatedAnalyticsQueryParams(
        assistant_id="a-1", client_source="chrome_extension", per_page=5
    )

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(_BODY)
        result = service.get_assistants_requests(params)

    assert isinstance(result, TabularResponse)
    assert result.data.rows == [{"request_id": "r-1", "assistant_id": "a-1"}]
    assert result.pagination.total_count == 1
    kwargs = get.call_args.kwargs
    assert kwargs["url"] == "https://api.example.com/v1/analytics/assistants-requests"
    assert kwargs["params"] == {
        "assistant_id": "a-1",
        "client_source": "chrome_extension",
        "page": 0,
        "per_page": 5,
    }


def test_get_assistants_requests_without_params_sends_no_query():
    service = AnalyticsService("https://api.example.com", "token")

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(_BODY)
        service.get_assistants_requests()

    assert get.call_args.kwargs["params"] == {}
