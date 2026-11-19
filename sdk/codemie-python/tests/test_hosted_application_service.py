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

"""Unit tests for the hosted application service: routes, headers and body shapes."""

import inspect
import logging
from unittest.mock import MagicMock, patch

import pytest
import requests
from pydantic import BaseModel

import codemie_sdk
from codemie_sdk.client.client import CodeMieClient
from codemie_sdk.models import hosted_application as hosted_models
from codemie_sdk.models.hosted_application import (
    HostedApplication,
    HostedApplicationCapabilities,
    HostedApplicationCategory,
    HostedApplicationDeletion,
    HostedApplicationList,
    HostedApplicationShareLink,
    HostedApplicationUploadReceipt,
    HostedApplicationValidationReport,
    HostedApplicationVersion,
    HostedApplicationVersionQueued,
    HostedApplicationVersionStart,
)
from codemie_sdk.services.hosted_application import HostedApplicationService

_BASE = "https://api.example.com/v1/hosted-applications"
_APP_ID = "11111111-1111-4111-8111-111111111111"
_VERSION_ID = "22222222-2222-4222-8222-222222222222"
_ETAG = f'"app:{_APP_ID}:3"'
_APP = {
    "id": _APP_ID,
    "name": "demo",
    "description": "demo app",
    "project": "demo-project",
    "shared": False,
    "is_global": False,
    "created_by": {"id": "u-1", "username": "owner", "name": "Owner"},
    "user_abilities": ["READ", "WRITE"],
    "etag": _ETAG,
    "revision": 3,
    "unknown_field": "ignored",
}


def _ok_response(body, status: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status
    response.content = b"{}"
    response.json.return_value = body
    return response


@pytest.fixture
def service() -> HostedApplicationService:
    return HostedApplicationService("https://api.example.com", "token")


def test_capabilities_parses_unavailable_account(service):
    body = {
        "create": False,
        "view": False,
        "disabled_reason": "Applications are not available for this account",
        "launch_policy": None,
        "limits": {},
    }

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(body)
        result = service.capabilities()

    assert get.call_args.kwargs["url"] == f"{_BASE}/capabilities"
    assert isinstance(result, HostedApplicationCapabilities)
    assert result.view is False
    assert result.disabled_reason == "Applications are not available for this account"


def test_list_applications_sends_scope_and_skips_unset_filters(service):
    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response({"items": [_APP], "next_cursor": None})
        result = service.list_applications(
            scope="shared", limit=5, created_by=None, status="draft"
        )

    assert get.call_args.kwargs["url"] == _BASE
    assert get.call_args.kwargs["params"] == {
        "scope": "shared",
        "q": "",
        "limit": 5,
        "sort": "updated_desc",
        "status": "draft",
    }
    assert isinstance(result, HostedApplicationList)
    assert result.items[0].id == _APP_ID
    assert result.items[0].created_by.username == "owner"


def test_get_thumbnail_returns_the_raw_response(service):
    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response({}, 204)
        result = service.get_thumbnail(_APP_ID)

    assert get.call_args.kwargs["url"] == f"{_BASE}/{_APP_ID}/thumbnail"
    assert result.status_code == 204


def test_create_application_sends_body_and_idempotency_key(service):
    with patch("codemie_sdk.utils.http.requests.request") as request:
        request.return_value = _ok_response(_APP, 201)
        result = service.create_application(
            "demo", "demo app", "demo-project", shared=True, idempotency_key="key-1"
        )

    kwargs = request.call_args.kwargs
    assert kwargs["method"] == "POST"
    assert kwargs["url"] == _BASE
    assert kwargs["json"] == {
        "name": "demo",
        "description": "demo app",
        "project": "demo-project",
        "shared": True,
    }
    assert kwargs["headers"]["Idempotency-Key"] == "key-1"
    assert kwargs["headers"]["Content-Type"] == "application/json"
    assert kwargs["headers"]["Authorization"] == "Bearer token"
    assert "If-Match" not in kwargs["headers"]
    assert isinstance(result, HostedApplication)
    assert result.etag == _ETAG


def test_changes_without_a_key_get_a_fresh_key_each_call(service):
    with patch("codemie_sdk.utils.http.requests.request") as request:
        request.return_value = _ok_response(_APP)
        service.activate(_APP_ID, _VERSION_ID, _ETAG)
        service.activate(_APP_ID, _VERSION_ID, _ETAG)

    keys = [
        call.kwargs["headers"]["Idempotency-Key"] for call in request.call_args_list
    ]
    assert len(set(keys)) == 2


def test_start_version_sends_hints_only_when_given(service):
    body = {
        "version_id": _VERSION_ID,
        "sequence": 1,
        "upload_id": "33333333-3333-4333-8333-333333333333",
        "generation": 1,
        "upload_etag": '"upload:x:1"',
        "version_etag": '"version:x:1"',
        "app_etag": _ETAG,
        "limits": {"byte_size": 12},
    }

    with patch("codemie_sdk.utils.http.requests.request") as request:
        request.return_value = _ok_response(body, 201)
        result = service.start_version(
            _APP_ID, "site.zip", "zip", 12, _ETAG, routing_mode="spa_history"
        )

    kwargs = request.call_args.kwargs
    assert kwargs["url"] == f"{_BASE}/{_APP_ID}/versions"
    assert kwargs["json"] == {
        "filename": "site.zip",
        "artifact_kind": "zip",
        "byte_size": 12,
        "routing_mode": "spa_history",
    }
    assert kwargs["headers"]["If-Match"] == _ETAG
    assert isinstance(result, HostedApplicationVersionStart)
    assert result.generation == 1


def test_upload_artifact_sends_raw_bytes_with_generation(service):
    body = {
        "upload_id": "33333333-3333-4333-8333-333333333333",
        "generation": 1,
        "state": "stored",
        "received_bytes": 5,
        "sha256": "a" * 64,
        "upload_etag": '"upload:x:2"',
        "version_etag": '"version:x:2"',
    }

    with patch("codemie_sdk.utils.http.requests.request") as request:
        request.return_value = _ok_response(body)
        result = service.upload_artifact(
            _APP_ID, _VERSION_ID, b"hello", '"upload:x:1"', 1
        )

    kwargs = request.call_args.kwargs
    assert kwargs["method"] == "PUT"
    assert kwargs["url"] == f"{_BASE}/{_APP_ID}/versions/{_VERSION_ID}/artifact"
    assert kwargs["data"] == b"hello"
    assert kwargs["json"] is None
    assert kwargs["headers"]["Content-Type"] == "application/octet-stream"
    assert kwargs["headers"]["If-Match"] == '"upload:x:1"'
    assert kwargs["headers"]["X-Upload-Generation"] == "1"
    assert isinstance(result, HostedApplicationUploadReceipt)
    assert result.state == "stored"


def test_complete_version_sends_receipt_fields(service):
    with patch("codemie_sdk.utils.http.requests.request") as request:
        request.return_value = _ok_response(
            {"job_id": "j-1", "state": "queued", "version_etag": '"version:x:3"'}, 202
        )
        result = service.complete_version(
            _APP_ID, _VERSION_ID, "up-1", "b" * 64, 1, '"version:x:2"'
        )

    kwargs = request.call_args.kwargs
    assert kwargs["url"] == f"{_BASE}/{_APP_ID}/versions/{_VERSION_ID}/complete"
    assert kwargs["json"] == {"generation": 1, "upload_id": "up-1", "sha256": "b" * 64}
    assert kwargs["headers"]["If-Match"] == '"version:x:2"'
    assert isinstance(result, HostedApplicationVersionQueued)
    assert result.state == "queued"


def test_get_version_and_validation_report_parse(service):
    version = {
        "id": _VERSION_ID,
        "sequence": 2,
        "validation_state": "awaiting_configuration",
        "can_activate": False,
    }
    report = {
        "state": "awaiting_configuration",
        "roots": ["a", "b"],
        "entries": ["a/index.html", "b/index.html"],
        "errors": [],
        "error_code": None,
        "configuration_revision": 1,
        "candidate_manifest_digest": "c" * 64,
    }

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(version)
        parsed = service.get_version(_APP_ID, _VERSION_ID)
        get.return_value = _ok_response(report)
        parsed_report = service.get_version_validation(_APP_ID, _VERSION_ID)

    assert isinstance(parsed, HostedApplicationVersion)
    assert parsed.validation_state == "awaiting_configuration"
    assert get.call_args.kwargs["url"].endswith(f"/versions/{_VERSION_ID}/validation")
    assert get.call_args.kwargs["params"] == {"offset": 0, "limit": 100}
    assert isinstance(parsed_report, HostedApplicationValidationReport)
    assert parsed_report.roots == ["a", "b"]


def test_configure_version_uses_put_with_choice(service):
    with patch("codemie_sdk.utils.http.requests.request") as request:
        request.return_value = _ok_response({"job_id": "j-2", "state": "queued"}, 202)
        service.configure_version(
            _APP_ID,
            _VERSION_ID,
            "a",
            "a/index.html",
            "static",
            "c" * 64,
            1,
            '"version:x:4"',
        )

    kwargs = request.call_args.kwargs
    assert kwargs["method"] == "PUT"
    assert kwargs["url"].endswith(f"/versions/{_VERSION_ID}/configuration")
    assert kwargs["json"] == {
        "site_root": "a",
        "entrypoint_path": "a/index.html",
        "routing_mode": "static",
        "candidate_manifest_digest": "c" * 64,
        "configuration_revision": 1,
    }
    assert kwargs["headers"]["If-Match"] == '"version:x:4"'


@pytest.mark.parametrize(
    ("method_name", "suffix"),
    [
        ("marketplace_publish", "marketplace/publish"),
        ("marketplace_unpublish", "marketplace/unpublish"),
    ],
)
def test_marketplace_calls_post_an_empty_body(service, method_name, suffix):
    with patch("codemie_sdk.utils.http.requests.request") as request:
        request.return_value = _ok_response(_APP)
        getattr(service, method_name)(_APP_ID, _ETAG)

    kwargs = request.call_args.kwargs
    assert kwargs["method"] == "POST"
    assert kwargs["url"] == f"{_BASE}/{_APP_ID}/{suffix}"
    assert kwargs["json"] == {}
    assert kwargs["headers"]["If-Match"] == _ETAG


def test_marketplace_publish_sends_the_categories(service):
    with patch("codemie_sdk.utils.http.requests.request") as request:
        request.return_value = _ok_response(_APP)
        service.marketplace_publish(
            _APP_ID, _ETAG, idempotency_key="key-1", categories=["cat-1", "cat-2"]
        )

    kwargs = request.call_args.kwargs
    assert kwargs["method"] == "POST"
    assert kwargs["url"] == f"{_BASE}/{_APP_ID}/marketplace/publish"
    assert kwargs["json"] == {"categories": ["cat-1", "cat-2"]}
    assert kwargs["headers"]["If-Match"] == _ETAG
    assert kwargs["headers"]["Idempotency-Key"] == "key-1"


def test_marketplace_publish_keeps_its_positional_arguments(service):
    with patch("codemie_sdk.utils.http.requests.request") as request:
        request.return_value = _ok_response(_APP)
        service.marketplace_publish(_APP_ID, _ETAG, "key-2")

    kwargs = request.call_args.kwargs
    assert kwargs["headers"]["Idempotency-Key"] == "key-2"
    assert kwargs["json"] == {}


def test_application_parses_its_categories(service):
    categories = [{"id": "cat-1", "name": "One"}, {"id": "cat-2", "name": "Two"}]
    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response({**_APP, "categories": categories})
        result = service.get_application(_APP_ID)

    assert result.categories == [
        HostedApplicationCategory(id="cat-1", name="One"),
        HostedApplicationCategory(id="cat-2", name="Two"),
    ]


def test_application_without_categories_has_an_empty_list():
    assert HostedApplication.model_validate(_APP).categories == []


def test_activate_and_select_version_send_the_version(service):
    with patch("codemie_sdk.utils.http.requests.request") as request:
        request.return_value = _ok_response(_APP)
        service.activate(_APP_ID, _VERSION_ID, _ETAG)
        activate_call = request.call_args
        service.select_version(_APP_ID, _VERSION_ID, _ETAG)
        select_call = request.call_args

    assert activate_call.kwargs["url"] == f"{_BASE}/{_APP_ID}/activate"
    assert select_call.kwargs["url"] == f"{_BASE}/{_APP_ID}/select-version"
    assert activate_call.kwargs["json"] == {"version_id": _VERSION_ID}
    assert select_call.kwargs["json"] == {"version_id": _VERSION_ID}


def test_share_and_unshare_send_user_ids_with_the_right_verbs(service):
    with (
        patch("codemie_sdk.utils.http.requests.post") as post,
        patch("codemie_sdk.utils.http.requests.delete") as delete,
    ):
        post.return_value = _ok_response({"shared_with": [{"id": "u-2"}]})
        delete.return_value = _ok_response({"shared_with": []})
        shared = service.share_with_users(_APP_ID, ["u-2"])
        unshared = service.unshare(_APP_ID, ["u-2"])

    assert post.call_args.kwargs["url"] == f"{_BASE}/{_APP_ID}/share"
    assert post.call_args.kwargs["json"] == {"user_ids": ["u-2"]}
    assert delete.call_args.kwargs["url"] == f"{_BASE}/{_APP_ID}/share"
    assert delete.call_args.kwargs["json"] == {"user_ids": ["u-2"]}
    assert shared.shared_with == [{"id": "u-2"}]
    assert unshared.shared_with == []


def test_share_link_calls_and_open_by_token(service):
    link = {"link": {"id": "l-1", "token": "tok", "created_at": "2026-01-01T00:00:00"}}
    with (
        patch("codemie_sdk.utils.http.requests.post") as post,
        patch("codemie_sdk.utils.http.requests.request") as request,
        patch("codemie_sdk.utils.http.requests.delete") as delete,
    ):
        post.return_value = _ok_response(link)
        request.return_value = _ok_response({"app_id": _APP_ID})
        delete.return_value = _ok_response({"link": None})
        created = service.create_share_link(_APP_ID)
        opened = service.open_share_link("tok")
        revoked = service.delete_share_link(_APP_ID)

    assert post.call_args.kwargs["url"] == f"{_BASE}/{_APP_ID}/share-link"
    assert isinstance(created, HostedApplicationShareLink)
    assert created.link.token == "tok"
    assert request.call_args.kwargs["method"] == "POST"
    assert request.call_args.kwargs["url"] == f"{_BASE}/share-links/open"
    assert request.call_args.kwargs["json"] == {"token": "tok"}
    assert opened.app_id == _APP_ID
    assert delete.call_args.kwargs["url"] == f"{_BASE}/{_APP_ID}/share-link"
    assert revoked.link is None


def test_open_share_link_does_not_log_the_token(service, caplog):
    secret = "share-link-secret-value"
    with (
        caplog.at_level(logging.DEBUG),
        patch("codemie_sdk.utils.http.requests.request") as request,
    ):
        request.return_value = _ok_response({"app_id": _APP_ID})
        service.open_share_link(secret)

    assert secret not in caplog.text


def test_read_calls_route_and_parse(service):
    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(_APP)
        application = service.get_application(_APP_ID)
        app_call = get.call_args.kwargs

        get.return_value = _ok_response({"items": [], "next_cursor": "c2"})
        versions = service.list_versions(_APP_ID, limit=5, cursor="c1")
        versions_call = get.call_args.kwargs

        get.return_value = _ok_response({"shared_with": [{"id": "u-2"}]})
        shared = service.shared_with(_APP_ID)
        shared_call = get.call_args.kwargs

        get.return_value = _ok_response({"users": [{"id": "u-3"}]})
        users = service.sharable_users(_APP_ID, "ann")
        users_call = get.call_args.kwargs

        get.return_value = _ok_response({"link": None})
        link = service.get_share_link(_APP_ID)
        link_call = get.call_args.kwargs

    assert app_call["url"] == f"{_BASE}/{_APP_ID}"
    assert isinstance(application, HostedApplication)
    assert application.id == _APP_ID
    assert versions_call["url"] == f"{_BASE}/{_APP_ID}/versions"
    assert versions_call["params"] == {"limit": 5, "cursor": "c1"}
    assert versions.next_cursor == "c2"
    assert shared_call["url"] == f"{_BASE}/{_APP_ID}/shared-with"
    assert shared.shared_with == [{"id": "u-2"}]
    assert users_call["url"] == f"{_BASE}/{_APP_ID}/sharable-users"
    assert users_call["params"] == {"q": "ann"}
    assert users.users == [{"id": "u-3"}]
    assert link_call["url"] == f"{_BASE}/{_APP_ID}/share-link"
    assert link.link is None


def test_delete_application_parses_the_accepted_answer(service):
    # The platform answers a delete with 202 and the purge state, not with an empty body.
    with patch("codemie_sdk.utils.http.requests.request") as request:
        request.return_value = _ok_response({"state": "purging", "job_id": "j-1"}, 202)
        deletion = service.delete_application(_APP_ID, _ETAG)

    assert request.call_args.kwargs["method"] == "DELETE"
    assert isinstance(deletion, HostedApplicationDeletion)
    assert deletion.state == "purging"


def test_request_returns_the_raw_response_when_asked(service):
    raw = _ok_response({}, 204)
    with patch("codemie_sdk.utils.http.requests.request", return_value=raw):
        result = service._api.request("GET", "/v1/anything", requests.Response)

    assert result is raw


def test_request_logs_the_call_but_not_the_body(service, caplog):
    secret = "body-secret-value"
    with (
        caplog.at_level(logging.DEBUG),
        patch("codemie_sdk.utils.http.requests.request") as request,
    ):
        request.return_value = _ok_response({"app_id": _APP_ID})
        service.open_share_link(secret)

    assert "Making POST request to" in caplog.text
    assert "Successfully processed POST request" in caplog.text
    assert secret not in caplog.text


def test_request_logs_the_failure_and_raises(service, caplog):
    failing = _ok_response({})
    failing.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
    with (
        caplog.at_level(logging.DEBUG),
        patch("codemie_sdk.utils.http.requests.request", return_value=failing),
        pytest.raises(requests.HTTPError),
    ):
        service.open_share_link("any-token")

    assert "Error during POST request" in caplog.text


def test_secret_fields_stay_out_of_repr_but_remain_readable():
    link = hosted_models.HostedApplicationShareLinkInfo(id="l-1", token="link-secret")
    launch = hosted_models.HostedApplicationLaunch(
        method="POST",
        version_id=_VERSION_ID,
        content_origin="https://v.example.com",
        action="https://v.example.com/_platform/launch",
        ticket="ticket-secret",
    )

    for shown in (repr(link), str(link), repr(launch), str(launch)):
        assert "link-secret" not in shown
        assert "ticket-secret" not in shown
    assert link.token == "link-secret"
    assert launch.ticket == "ticket-secret"


def test_every_hosted_model_is_exported_from_the_package():
    models = {
        name
        for name, value in vars(hosted_models).items()
        if inspect.isclass(value)
        and issubclass(value, BaseModel)
        and value.__module__ == hosted_models.__name__
    }

    assert models
    assert models <= set(codemie_sdk.__all__)
    assert all(hasattr(codemie_sdk, name) for name in models)


def test_launch_sends_purpose_and_optional_fields_only_when_given(service):
    body = {
        "method": "POST",
        "version_id": _VERSION_ID,
        "content_origin": "https://v.example.com",
        "action": "https://v.example.com/_platform/launch",
        "ticket": "t" * 43,
    }
    with patch("codemie_sdk.utils.http.requests.post") as post:
        post.return_value = _ok_response(body)
        result = service.launch(_APP_ID)
        plain = post.call_args.kwargs["json"]
        service.launch(_APP_ID, "owner_preview", version_id=_VERSION_ID, path="/a")

    assert plain == {"purpose": "published_view"}
    assert post.call_args.kwargs["json"] == {
        "purpose": "owner_preview",
        "version_id": _VERSION_ID,
        "path": "/a",
    }
    assert post.call_args.kwargs["url"] == f"{_BASE}/{_APP_ID}/launch"
    assert result.action.endswith("/_platform/launch")


def test_delete_application_and_deletion_status(service):
    with (
        patch("codemie_sdk.utils.http.requests.request") as request,
        patch("codemie_sdk.utils.http.requests.get") as get,
    ):
        request.return_value = _ok_response(
            {"state": "purging", "job_id": "j-3", "application": _APP}, 202
        )
        get.return_value = _ok_response(
            {"state": "purged", "app_id": _APP_ID, "remaining_prefixes": 0}
        )
        deletion = service.delete_application(_APP_ID, _ETAG, idempotency_key="k")
        status = service.deletion_status(_APP_ID)

    assert request.call_args.kwargs["method"] == "DELETE"
    assert request.call_args.kwargs["url"] == f"{_BASE}/{_APP_ID}"
    assert request.call_args.kwargs["headers"]["If-Match"] == _ETAG
    assert isinstance(deletion, HostedApplicationDeletion)
    assert get.call_args.kwargs["url"] == f"{_BASE}/{_APP_ID}/deletion-status"
    assert status.state == "purged"


def test_suspend_and_reinstate_use_the_admin_route(service):
    with patch("codemie_sdk.utils.http.requests.request") as request:
        request.return_value = _ok_response(_APP)
        service.suspend_application(_APP_ID, "policy review")
        suspend = request.call_args
        service.reinstate_application(_APP_ID, "checked", _ETAG)
        reinstate = request.call_args

    base = f"https://api.example.com/v1/admin/hosted-applications/{_APP_ID}/security"
    assert suspend.kwargs["url"] == f"{base}/suspend"
    assert suspend.kwargs["json"] == {"reason": "policy review"}
    assert "If-Match" not in suspend.kwargs["headers"]
    assert reinstate.kwargs["url"] == f"{base}/reinstate"
    assert reinstate.kwargs["json"] == {"reason": "checked"}
    assert reinstate.kwargs["headers"]["If-Match"] == _ETAG


def test_with_token_returns_a_service_for_another_caller(service):
    other = service.with_token("other-token")

    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(
            {
                "byte_limit": 10,
                "available_bytes": 10,
                "stored_bytes": 0,
                "reserved_bytes": 0,
            }
        )
        other.usage()

    assert get.call_args.kwargs["headers"]["Authorization"] == "Bearer other-token"
    assert other is not service


def test_client_exposes_the_service():
    with patch("codemie_sdk.client.client.KeycloakCredentials") as credentials:
        credentials.return_value.get_token.return_value = "t"
        client = CodeMieClient(
            auth_server_url="https://auth.example.com",
            auth_realm_name="realm",
            codemie_api_domain="https://api.example.com",
            auth_client_id="id",
            auth_client_secret="secret",
        )

    assert isinstance(client.hosted_applications, HostedApplicationService)
