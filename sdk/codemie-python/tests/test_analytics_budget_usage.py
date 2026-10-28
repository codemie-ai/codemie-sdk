from unittest.mock import MagicMock, patch

from codemie_sdk.models.analytics import TabularResponse
from codemie_sdk.services.analytics import AnalyticsService

_TABULAR_BODY = {
    "data": {
        "columns": [{"id": "project_name", "label": "Project", "type": "string"}],
        "rows": [{"project_name": "demo-project"}],
    },
    "metadata": {
        "timestamp": "2026-01-01T00:00:00Z",
        "data_as_of": "2026-01-01T00:00:00Z",
        "filters_applied": {},
        "execution_time_ms": 1.0,
    },
}


def _ok_response(body: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = body
    return response


def test_get_budget_usage_requests_endpoint_and_parses_rows():
    service = AnalyticsService("https://api.example.com", "token")

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(_TABULAR_BODY)
        result = service.get_budget_usage()

    kwargs = get.call_args.kwargs
    assert kwargs["url"] == "https://api.example.com/v1/analytics/budget_usage"
    assert kwargs["headers"]["Authorization"] == "Bearer token"
    assert not kwargs["params"]
    assert isinstance(result, TabularResponse)
    assert result.data.rows == [{"project_name": "demo-project"}]


def test_get_user_project_spending_sends_users_param_and_parses_rows():
    service = AnalyticsService("https://api.example.com", "token")

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(_TABULAR_BODY)
        result = service.get_user_project_spending("a@example.com")

    kwargs = get.call_args.kwargs
    assert kwargs["url"] == "https://api.example.com/v1/analytics/user-project-spending"
    assert kwargs["params"] == {"users": "a@example.com"}
    assert isinstance(result, TabularResponse)
    assert result.data.rows == [{"project_name": "demo-project"}]
