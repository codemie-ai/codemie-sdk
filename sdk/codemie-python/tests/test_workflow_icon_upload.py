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

"""Tests for WorkflowService.upload_icon(), faking the network layer at ``_api``."""

from types import SimpleNamespace

import pytest

from codemie_sdk.services.workflow import WorkflowService


class DummyApi:
    def __init__(self, response: dict):
        self.last_call = SimpleNamespace(endpoint=None, response_model=None, files=None)
        self._response = response

    def post_multipart(self, endpoint, response_model, files=None, **kwargs):
        self.last_call.endpoint = endpoint
        self.last_call.response_model = response_model
        self.last_call.files = files
        return self._response


@pytest.fixture
def service():
    service = WorkflowService("https://api.example.com", "token")
    service._api = DummyApi({"file_url": "stored-file-url"})
    return service


def test_upload_icon_posts_file_to_icon_endpoint(service, tmp_path):
    icon = tmp_path / "icon.png"
    icon.write_bytes(b"icon-bytes")

    result = service.upload_icon(icon)

    assert result == {"file_url": "stored-file-url"}
    assert service._api.last_call.endpoint == "/v1/workflows/icon"
    assert service._api.last_call.response_model is dict
    assert service._api.last_call.files == [
        ("file", ("icon.png", b"icon-bytes", "image/png"))
    ]


def test_upload_icon_declared_content_type_overrides_guess(service, tmp_path):
    icon = tmp_path / "icon.png"
    icon.write_bytes(b"icon-bytes")

    service.upload_icon(icon, content_type="image/jpeg")

    assert service._api.last_call.files == [
        ("file", ("icon.png", b"icon-bytes", "image/jpeg"))
    ]


def test_upload_icon_unknown_extension_falls_back_to_octet_stream(service, tmp_path):
    icon = tmp_path / "icon.unknownext"
    icon.write_bytes(b"icon-bytes")

    service.upload_icon(icon)

    assert service._api.last_call.files == [
        ("file", ("icon.unknownext", b"icon-bytes", "application/octet-stream"))
    ]
