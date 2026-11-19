from unittest.mock import MagicMock, patch

import pytest
from requests import HTTPError

from codemie_sdk.models.analytics import (
    AnalyticsDetailResponse,
    CliInsightsUserDetailQueryParams,
)
from codemie_sdk.services.analytics import AnalyticsService

_DETAIL_BODY = {
    "data": {"user_name": "jane@example.com", "total_sessions": 0, "repositories": []},
    "metadata": {
        "timestamp": "2026-01-01T00:00:00Z",
        "data_as_of": "2026-01-01T00:00:00Z",
        "filters_applied": {},
        "execution_time_ms": 1.0,
    },
}


def _response(status_code: int, body: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = body
    response.raise_for_status.side_effect = (
        HTTPError(response=response) if status_code >= 400 else None
    )
    return response


def test_get_cli_insights_user_detail_requests_endpoint_and_parses_detail():
    service = AnalyticsService("https://api.example.com", "token")
    params = CliInsightsUserDetailQueryParams(
        user_name="jane@example.com", user_id="u-1", time_period="last_7_days"
    )

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _response(200, _DETAIL_BODY)
        result = service.get_cli_insights_user_detail(params)

    kwargs = get.call_args.kwargs
    assert kwargs["url"] == (
        "https://api.example.com/v1/analytics/cli-insights-user-detail"
    )
    assert kwargs["headers"]["Authorization"] == "Bearer token"
    assert kwargs["params"] == {
        "user_name": "jane@example.com",
        "user_id": "u-1",
        "time_period": "last_7_days",
    }
    assert isinstance(result, AnalyticsDetailResponse)
    assert result.data == {
        "user_name": "jane@example.com",
        "total_sessions": 0,
        "repositories": [],
    }


def test_get_cli_insights_user_detail_omits_unset_user_id():
    service = AnalyticsService("https://api.example.com", "token")

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _response(200, _DETAIL_BODY)
        service.get_cli_insights_user_detail(
            CliInsightsUserDetailQueryParams(user_name="jane")
        )

    assert get.call_args.kwargs["params"] == {"user_name": "jane"}


def test_get_cli_insights_user_detail_raises_on_unmatched_user():
    service = AnalyticsService("https://api.example.com", "token")

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _response(
            404, {"error": {"message": "User ghost not found."}}
        )
        with pytest.raises(HTTPError) as error:
            service.get_cli_insights_user_detail(
                CliInsightsUserDetailQueryParams(user_name="ghost")
            )

    assert error.value.response.status_code == 404


def test_cli_insights_user_detail_params_require_user_name():
    with pytest.raises(ValueError):
        CliInsightsUserDetailQueryParams()


@pytest.mark.parametrize("user_name", ["", "   ", " \t "])
def test_cli_insights_user_detail_params_reject_blank_user_name(user_name):
    with pytest.raises(ValueError):
        CliInsightsUserDetailQueryParams(user_name=user_name)


def test_cli_insights_user_detail_params_strip_user_name():
    params = CliInsightsUserDetailQueryParams(user_name="  jane@example.com  ")

    assert params.user_name == "jane@example.com"


def test_cli_insights_user_detail_params_reject_users_filter():
    with pytest.raises(ValueError, match="users"):
        CliInsightsUserDetailQueryParams(user_name="jane", users="u-2,u-3")
