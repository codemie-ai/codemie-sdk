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

"""Unit tests for the include_all query parameter of LLMService.list."""

from unittest.mock import MagicMock, patch

from codemie_sdk.models.llm import LLMModel
from codemie_sdk.services.llm import LLMService


def _service():
    with patch("codemie_sdk.services.llm.ApiRequestHandler") as handler_cls:
        service = LLMService("https://example.test", "token")
    return service, handler_cls.return_value


def test_list_omits_include_all_by_default():
    service, api = _service()
    api.get = MagicMock(return_value=[])

    service.list()

    api.get.assert_called_once_with(
        "/v1/llm_models", list[LLMModel], params=None, wrap_response=False
    )


def test_list_sends_include_all_true():
    service, api = _service()
    api.get = MagicMock(return_value=[])

    service.list(include_all=True)

    api.get.assert_called_once_with(
        "/v1/llm_models",
        list[LLMModel],
        params={"include_all": "true"},
        wrap_response=False,
    )
