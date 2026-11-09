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


def test_send_cli_hook_events_sends_project_header_when_given():
    service = AnalyticsService("https://api.example.com", "token")

    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = _ok_response({})
        service.send_cli_hook_events([{"type": "agent.session.start"}], project="p")

    headers = post.call_args.kwargs["headers"]
    assert headers["X-CodeMie-Project"] == "p"
    assert headers["Content-Type"] == "application/x-ndjson"


def test_send_cli_hook_events_omits_project_header_by_default():
    service = AnalyticsService("https://api.example.com", "token")

    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = _ok_response({})
        service.send_cli_hook_events([{"type": "agent.session.start"}])

    assert "X-CodeMie-Project" not in post.call_args.kwargs["headers"]


def test_ingest_event_hooks_sends_project_header_on_every_event():
    service = AnalyticsService("https://api.example.com", "token")

    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = _ok_response({})
        service.ingest_cli_analytics_event_hooks(
            [{"type": "a"}, {"type": "b"}], project="p"
        )

    assert post.call_count == 2
    for call in post.call_args_list:
        assert call.kwargs["headers"]["X-CodeMie-Project"] == "p"
        assert call.kwargs["headers"]["Content-Type"] == "application/x-ndjson"


def test_ingest_event_hooks_and_logs_omit_project_header_by_default():
    service = AnalyticsService("https://api.example.com", "token")

    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = _ok_response({})
        service.ingest_cli_analytics_event_hooks([{"type": "a"}])
        service.ingest_cli_analytics_logs({"resourceLogs": []})

    assert len(post.call_args_list) == 2
    for call in post.call_args_list:
        assert "X-CodeMie-Project" not in call.kwargs["headers"]


def test_ingest_logs_sends_project_header_when_given():
    service = AnalyticsService("https://api.example.com", "token")

    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = _ok_response({})
        service.ingest_cli_analytics_logs({"resourceLogs": []}, project="p")

    kwargs = post.call_args.kwargs
    assert kwargs["url"] == "https://api.example.com/v1/analytics/cli-analytics/logs"
    assert kwargs["headers"]["X-CodeMie-Project"] == "p"


def test_send_cli_hook_events_returns_discard_body_unchanged():
    service = AnalyticsService("https://api.example.com", "token")
    discard = {"accepted": 0, "dropped": 2, "reason": "cli_analytics_disabled"}

    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = _ok_response(discard)
        result = service.send_cli_hook_events([{"type": "a"}, {"type": "b"}], "p")

    assert result == discard


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
