import json
from unittest.mock import patch

import pytest
import requests

from codemie_sdk.exceptions import ToolkitNotApprovedError
from codemie_sdk.models.assistant import VirtualAssistantChatRequest
from codemie_sdk.services.assistant import AssistantService
from codemie_sdk.utils.http import ApiRequestHandler

TOOL_MSG = (
    "Tool 'write_file' in toolkit 'FileSystem' is not approved by platform policy."
)
TOOLKIT_MSG = "Toolkit 'Git' is not approved by platform policy."


def make_response(status=400, body=None, raw=None):
    response = requests.Response()
    response.status_code = status
    if raw is not None:
        response._content = raw
    else:
        response._content = json.dumps(body).encode()
    return response


def error_body(message):
    return {"error": {"message": message}}


def handler():
    return ApiRequestHandler("https://api.example.com", "token")


def put_with(response):
    with patch("requests.put", return_value=response):
        return handler().put("/v1/x", dict, json_data={})


def test_tool_level_refusal_parsed():
    response = make_response(body=error_body(TOOL_MSG))
    with pytest.raises(ToolkitNotApprovedError) as exc:
        put_with(response)
    err = exc.value
    assert err.toolkit == "FileSystem"
    assert err.tool == "write_file"
    assert err.message == TOOL_MSG
    assert err.policy == "toolkit-management policy"
    assert err.status_code == 400
    assert err.response is response
    assert isinstance(err, requests.HTTPError)
    text = str(err)
    assert (
        TOOL_MSG in text
        and "write_file" in text
        and "toolkit-management policy" in text
    )


def test_toolkit_level_refusal_parsed():
    with pytest.raises(ToolkitNotApprovedError) as exc:
        put_with(make_response(body=error_body(TOOLKIT_MSG)))
    assert exc.value.toolkit == "Git"
    assert exc.value.tool is None
    assert "Git" in str(exc.value)


def test_top_level_message_form():
    with pytest.raises(ToolkitNotApprovedError) as exc:
        put_with(make_response(body={"message": TOOL_MSG}))
    assert exc.value.tool == "write_file"


def test_non_matching_400_is_plain_http_error():
    with pytest.raises(requests.HTTPError) as exc:
        put_with(make_response(body=error_body("Duplicate toolkit")))
    assert not isinstance(exc.value, ToolkitNotApprovedError)


@pytest.mark.parametrize("status", [403, 500])
def test_other_statuses_are_plain_http_error(status):
    with pytest.raises(requests.HTTPError) as exc:
        put_with(make_response(status=status, body=error_body(TOOL_MSG)))
    assert not isinstance(exc.value, ToolkitNotApprovedError)


def test_non_json_body_is_plain_http_error():
    with pytest.raises(requests.HTTPError) as exc:
        put_with(make_response(raw=b"<html>bad</html>"))
    assert not isinstance(exc.value, ToolkitNotApprovedError)


def test_empty_body_is_plain_http_error():
    with pytest.raises(requests.HTTPError) as exc:
        put_with(make_response(raw=b""))
    assert not isinstance(exc.value, ToolkitNotApprovedError)


@pytest.mark.parametrize("stream", [False, True])
def test_ask_virtual_surfaces_error(stream):
    service = AssistantService("https://api.example.com", "token")
    request = VirtualAssistantChatRequest(text="hi", stream=stream)
    with patch("requests.post", return_value=make_response(body=error_body(TOOL_MSG))):
        with pytest.raises(ToolkitNotApprovedError):
            service.ask_virtual(request)