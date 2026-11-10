from types import SimpleNamespace

from codemie_sdk.services.assistant import AssistantService
from codemie_sdk.models.assistant import (
    SharedWithResponse,
    SharableUsersResponse,
)


class DummyApi:
    """Mimics ApiRequestHandler: parses the raw payload into response_model,
    the same way the real GET/POST/DELETE helpers do via _parse_response."""

    def __init__(self):
        self.last_call = SimpleNamespace(
            endpoint=None, params=None, json_data=None, method=None
        )

    def _raw(self, endpoint):
        if endpoint.endswith("/shared-with"):
            return {
                "shared_with": [
                    {
                        "id": "u1",
                        "username": "alice",
                        "email": "alice@example.com",
                        "name": "Alice",
                        "picture": None,
                    }
                ]
            }
        if endpoint.endswith("/sharable-users"):
            return {
                "users": [
                    {
                        "id": "u2",
                        "username": "bob",
                        "email": "bob@example.com",
                        "name": "Bob",
                        "picture": None,
                    }
                ]
            }
        return {}

    def get(self, endpoint, response_model, params=None, wrap_response=True):
        self.last_call.method = "GET"
        self.last_call.endpoint = endpoint
        self.last_call.params = params or {}
        return response_model.model_validate(self._raw(endpoint))

    def post(self, endpoint, response_model, json_data=None, wrap_response=True):
        self.last_call.method = "POST"
        self.last_call.endpoint = endpoint
        self.last_call.json_data = json_data
        payload = {
            "shared_with": [
                {"id": uid, "username": uid} for uid in json_data["user_ids"]
            ]
        }
        return response_model.model_validate(payload)

    def delete(
        self, endpoint, response_model, params=None, json_data=None, wrap_response=True
    ):
        self.last_call.method = "DELETE"
        self.last_call.endpoint = endpoint
        self.last_call.json_data = json_data
        return response_model.model_validate({"shared_with": []})


def test_list_shared_with_calls_correct_endpoint():
    service = AssistantService("https://api.example.com", "token")
    dummy_api = DummyApi()
    service._api = dummy_api

    res = service.list_shared_with("assistant-123")

    assert dummy_api.last_call.endpoint == "/v1/assistants/assistant-123/shared-with"
    assert isinstance(res, SharedWithResponse)
    assert res.shared_with[0].username == "alice"


def test_share_posts_user_ids_and_maps_response():
    service = AssistantService("https://api.example.com", "token")
    dummy_api = DummyApi()
    service._api = dummy_api

    res = service.share("assistant-123", ["u1", "u2"])

    assert dummy_api.last_call.endpoint == "/v1/assistants/assistant-123/share"
    assert dummy_api.last_call.json_data == {"user_ids": ["u1", "u2"]}
    assert isinstance(res, SharedWithResponse)
    assert [u.id for u in res.shared_with] == ["u1", "u2"]


def test_revoke_share_sends_delete_with_body():
    service = AssistantService("https://api.example.com", "token")
    dummy_api = DummyApi()
    service._api = dummy_api

    res = service.revoke_share("assistant-123", ["u1"])

    assert dummy_api.last_call.method == "DELETE"
    assert dummy_api.last_call.endpoint == "/v1/assistants/assistant-123/share"
    assert dummy_api.last_call.json_data == {"user_ids": ["u1"]}
    assert isinstance(res, SharedWithResponse)
    assert res.shared_with == []


def test_search_sharable_users_calls_correct_endpoint_with_query():
    service = AssistantService("https://api.example.com", "token")
    dummy_api = DummyApi()
    service._api = dummy_api

    res = service.search_sharable_users("assistant-123", "bo")

    assert dummy_api.last_call.endpoint == "/v1/assistants/assistant-123/sharable-users"
    assert dummy_api.last_call.params == {"q": "bo"}
    assert isinstance(res, SharableUsersResponse)
    assert res.users[0].username == "bob"
