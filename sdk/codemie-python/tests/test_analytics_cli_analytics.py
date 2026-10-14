import json
from unittest.mock import MagicMock, patch

from codemie_sdk.services.analytics import AnalyticsService


def _ok_response(body: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = body
    return response


def test_send_cli_hook_events_posts_ndjson_with_auth():
    service = AnalyticsService("https://api.example.com", "token")
    events = [
        {"type": "agent.session.start", "session_id": "s1"},
        {"type": "agent.usage.request", "session_id": "s1", "input_tokens": 1},
    ]

    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = _ok_response({})
        result = service.send_cli_hook_events(events)

    assert result == {}
    kwargs = post.call_args.kwargs
    assert kwargs["url"] == (
        "https://api.example.com/v1/analytics/cli-analytics/event-hooks"
    )
    assert kwargs["headers"]["Content-Type"] == "application/x-ndjson"
    assert kwargs["headers"]["Authorization"] == "Bearer token"
    assert kwargs["json"] is None
    lines = kwargs["data"].decode("utf-8").splitlines()
    assert [json.loads(line) for line in lines] == events


def test_get_cli_sessions_passes_query_params():
    service = AnalyticsService("https://api.example.com", "token")
    body = {"data": {"sessions": [], "page": 0, "per_page": 20, "total": 0}}

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(body)
        result = service.get_cli_sessions(search="autotest/repo", per_page=20)

    assert result == body
    kwargs = get.call_args.kwargs
    assert (
        kwargs["url"] == "https://api.example.com/v1/analytics/cli-analytics/sessions"
    )
    assert kwargs["params"] == {"search": "autotest/repo", "per_page": 20}
