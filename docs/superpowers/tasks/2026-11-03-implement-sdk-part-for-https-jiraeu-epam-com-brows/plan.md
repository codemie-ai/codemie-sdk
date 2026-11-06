# EPMCDME-16484 Run Attributes (SDK part) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mirror the backend run-attributes contract in both SDKs: `attributes` filter on 2 existing analytics endpoints, 3 new analytics endpoints, and `attributes` on chat/workflow-execution create bodies and conversation/execution responses.

**Architecture:** Dedicated params models/schemas extend the paginated one and are used only by the 5 supporting endpoints (the shared paginated class is untouched). `attributes` is a dict in the SDK API and is JSON-encoded in the params layer (Python `field_serializer`, Node service helper) so the transports do not mangle it. Body/response `attributes` is a plain `dict[str, str]` / `Record<string, string>`.

**Tech Stack:** Python (pydantic v2, pytest, ruff) in `sdk/codemie-python`; TypeScript (zod 4, jest 29 + ts-jest, Biome) in `sdk/codemie-nodejs`.

**Spec:** none (inline requirements). Backend source of truth: `/Users/bohdan_maliar/Projects/codemie-dev/codemie`, branch `EPMCDME-16484_run-attributes` (read-only). Research: `technical-analysis.md` in this directory.

**Commits:** Commit per task using the repository's existing convention (`feat(python): ...` / `feat(nodejs): ...` style; check `git log`). Do not commit as part of planning.

## Acceptance criteria

- [ ] Both SDKs: `assistants-chats` and `workflows` getters accept `attributes` (dict) and send it as a JSON string query param, e.g. `{"team": "alpha"}`.
- [ ] Both SDKs expose `assistants-requests` (`client_source`, `assistant_id`, `attributes`), `workflows-executions` (`client_source`, `attributes`) and `attributes-usage` (`attribute_key`, `client_source`, `attributes`) getters, all GET, returning the existing `TabularResponse`, with the common paginated params.
- [ ] The other ~19 analytics getters do not accept or send `attributes` (shared paginated params class/schema unchanged).
- [ ] Both SDKs: chat create request and workflow-execution create request accept `attributes` (dict of str to str) and send it in the JSON body; conversation details and workflow execution responses expose `attributes` (absent/null tolerated).
- [ ] New exports are reachable from the Python package root and the Node barrels.
- [ ] Mock tests in both SDKs prove JSON-string serialization of `attributes` on the wire-facing call (Python `requests.get` params, Node `api.get` params).

## Global Constraints

- Backend facts: `attributes` query param is `str | None`, a JSON object of string keys/values; invalid -> HTTP 422; blank/`{}` = no filter. Key `^[a-z0-9][a-z0-9._-]{0,62}[a-z0-9]$`, no `codemie.`/`otel.` prefix, max 4 keys (env-configurable), value 1-128 chars. **SDKs do not validate these**; the backend returns 422.
- Decision `attribute_key`: backend declares it optional but returns 422 when missing, so both SDKs make it **required** (Python required pydantic field; Node non-optional zod string). No format validation client-side.
- Decision `client_source`: plain optional string (backend enum: `platform`, `ms-teams-bot`, `chrome_extension`, `other`; unknown values -> backend 422; list them in the field description only).
- Decision scope of body/response: backend `attributes` exists on `AssistantChatRequest` (`core/models.py:726`), `CreateWorkflowExecutionRequest` (`workflow_execution.py:350`), `ConversationResponse` (`conversation.py:992`), `WorkflowExecutionResponse` (`workflow_execution.py:309`) only. Do not add it to `VirtualAssistantChatRequest`, `ConversationCreateRequest`, the conversation list item (`Conversation`), or any other model.
- Do not touch the stale `last_90_days` description string in Python `AnalyticsQueryParams`. No README/CHANGELOG changes (no analytics docs exist). No version bumps.
- Follow existing style: Python black-style 88 cols + ruff; Node Biome (`npm run lint`).

## Review Focus

- Attribute value with quotes/non-ASCII (e.g. `{"team": "ålpha \"x\""}`) must round-trip through `json.loads` / `JSON.parse` of the sent string (tests in Tasks 1, 2).
- `attributes` omitted or `None` must send no `attributes` param at all (Tasks 1, 2).
- `attributes={}` sends `"{}"` (backend treats it as no filter); no special-casing (Tasks 1, 2).
- `attributes-usage` without `attribute_key` fails at the SDK boundary (pydantic `ValidationError` / `ZodError`), not as a late 422 (Tasks 1, 2).
- Responses from an older backend without `attributes` (or with `null`) still parse (Tasks 3, 4).

---

### Task 1: Python analytics params, methods, exports

**Files:**
- Modify: `sdk/codemie-python/src/codemie_sdk/models/analytics.py` (add after `PaginatedAnalyticsQueryParams`, ~line 149; add `import json` and `field_serializer` to pydantic import)
- Modify: `sdk/codemie-python/src/codemie_sdk/services/analytics.py` (`get_assistants_chats` line 75, `get_workflows` line 95; add three methods after `get_workflows`)
- Modify: `sdk/codemie-python/src/codemie_sdk/__init__.py` (import block ~line 97, `__all__` ~line 267)
- Test: `sdk/codemie-python/tests/test_analytics_attributes.py` (create)

**Interfaces:**
- Produces (models, all `extra="ignore"`, inherit the paginated defaults page=0, per_page=20):
  - `AttributesAnalyticsQueryParams(PaginatedAnalyticsQueryParams)`: `client_source: str | None = None`, `attributes: dict[str, str] | None = None`.
  - `AssistantsRequestsQueryParams(AttributesAnalyticsQueryParams)`: `assistant_id: str | None = None`.
  - `AttributesUsageQueryParams(AttributesAnalyticsQueryParams)`: `attribute_key: str` (required).
- Produces (service): `get_assistants_requests(params: AssistantsRequestsQueryParams | None = None) -> TabularResponse`, `get_workflows_executions(params: AttributesAnalyticsQueryParams | None = None) -> TabularResponse`, `get_attributes_usage(params: AttributesUsageQueryParams) -> TabularResponse`. Existing `get_assistants_chats` / `get_workflows` params annotation becomes `AttributesAnalyticsQueryParams | PaginatedAnalyticsQueryParams | None` (keeps old callers type-valid).

- [ ] **Step 1: Write failing tests** in `tests/test_analytics_attributes.py` using `patch("codemie_sdk.utils.http.requests.get")` and a `_ok_response(body)` helper like `tests/test_analytics_cli_analytics.py:7`. The body must satisfy `TabularResponse`: `{"data": {"columns": [], "rows": []}, "metadata": {"timestamp": "t", "data_as_of": "t", "filters_applied": {}, "execution_time_ms": 1}}`. Tests (assert on `get.call_args.kwargs["url"|"params"]`, base `https://api.example.com`):
  - `test_assistants_chats_sends_attributes_as_json_string`: `AttributesAnalyticsQueryParams(attributes={"team": "alpha"})` -> `params["attributes"]` is a `str` and `json.loads(...) == {"team": "alpha"}`; url ends `/v1/analytics/assistants-chats`.
  - `test_workflows_sends_attributes_as_json_string`: same for `/v1/analytics/workflows`.
  - `test_attributes_roundtrip_non_ascii_and_quotes`: value `'ålpha "x"'` round-trips via `json.loads`.
  - `test_attributes_omitted_when_none`: no `attributes` key in params; `page == 0`, `per_page == 20` present.
  - `test_empty_attributes_sends_empty_object_string`: `params["attributes"] == "{}"`.
  - `test_assistants_requests_endpoint_and_params`: url `/v1/analytics/assistants-requests`; `client_source="platform"`, `assistant_id="a1"`, attributes JSON string all in params.
  - `test_workflows_executions_endpoint`: url `/v1/analytics/workflows-executions`; client_source + attributes sent.
  - `test_attributes_usage_requires_attribute_key`: `pytest.raises(ValidationError)` on `AttributesUsageQueryParams()`.
  - `test_attributes_usage_endpoint_and_params`: url `/v1/analytics/attributes-usage`, `params["attribute_key"] == "team"`, attributes JSON string.
  - `test_shared_paginated_params_has_no_attributes_field`: `"attributes" not in PaginatedAnalyticsQueryParams.model_fields` and `get_tools_usage(PaginatedAnalyticsQueryParams())` sends no `attributes`.
  - `test_new_symbols_exported_from_package_root`: `from codemie_sdk import AttributesAnalyticsQueryParams, AssistantsRequestsQueryParams, AttributesUsageQueryParams`.
- [ ] **Step 2: Run to verify failure**: `cd sdk/codemie-python && python -m pytest tests/test_analytics_attributes.py -v` -> FAIL (ImportError).
- [ ] **Step 3: Implement the three models** in `models/analytics.py`. The `attributes` JSON encoding lives in a `@field_serializer("attributes")` on `AttributesAnalyticsQueryParams` returning `json.dumps(value)` for a non-None dict (None is already dropped by the service's `model_dump(exclude_none=True)`). Descriptions: attributes = "Run attributes filter; sent as a JSON string, e.g. {\"team\": \"alpha\"}. All pairs must match."; client_source lists the four backend values.
- [ ] **Step 4: Implement service methods** in `services/analytics.py` following the existing getter pattern exactly (`params.model_dump(exclude_none=True) if params else {}`, `self._api.get(path, TabularResponse, params=..., wrap_response=False)`); docstrings in the existing style. For `get_attributes_usage`, `params` is required (no default). Update the two existing getters' annotations/docstring args only.
- [ ] **Step 5: Export** the three models in `__init__.py` import block and `__all__` next to `PaginatedAnalyticsQueryParams`.
- [ ] **Step 6: Verify**: `python -m pytest tests/test_analytics_attributes.py tests/test_analytics_cli_analytics.py -v` -> PASS; `ruff check src tests && ruff format --check src tests` clean.

Test-first: yes — `test_assistants_chats_sends_attributes_as_json_string` fails (ImportError / dict sent instead of JSON string) before the models and serializer exist.

---

### Task 2: Node analytics schemas, methods, tests

**Files:**
- Modify: `sdk/codemie-nodejs/src/schemas/analytics.ts` (append after `PaginatedAnalyticsQueryParams` type, line 40)
- Modify: `sdk/codemie-nodejs/src/services/analytics.ts` (`getAssistantsChats` line 33, `getWorkflows` line 40; add three methods after `getWorkflows`; add a module-private helper)
- Test: `sdk/codemie-nodejs/tests/unit/services/analytics.test.ts` (create)
- No barrel edits: `src/schemas/index.ts` already `export *`; confirm `schemas/analytics` is re-exported there, add the line only if missing.

**Interfaces:**
- Produces (schemas, `.readonly()`, built with `analyticsQueryParamsBase.extend({...})`, same `page`/`per_page` defaults as the paginated schema):
  - `AttributesAnalyticsQueryParamsSchema`: adds `client_source: z.string().optional()`, `attributes: z.record(z.string(), z.string()).optional()`. Type `AttributesAnalyticsQueryParams = Partial<z.infer<...>>`.
  - `AssistantsRequestsQueryParamsSchema`: adds `assistant_id: z.string().optional()` on top. Type `AssistantsRequestsQueryParams = Partial<z.infer<...>>`.
  - `AttributesUsageQueryParamsSchema`: adds `attribute_key: z.string()` (required). Type `AttributesUsageQueryParams = z.input<...>` (not Partial, so the key stays required).
- Produces (service): `getAssistantsRequests(_params: AssistantsRequestsQueryParams = {})`, `getWorkflowsExecutions(_params: AttributesAnalyticsQueryParams = {})`, `getAttributesUsage(_params: AttributesUsageQueryParams)`, all `Promise<TabularResponse>`. `getAssistantsChats`/`getWorkflows` now parse `AttributesAnalyticsQueryParamsSchema`.

- [ ] **Step 1: Write failing tests** in `tests/unit/services/analytics.test.ts`, following `tests/unit/services/llm.test.ts` (`jest.mock("../../../src/utils/http", () => ({ ApiRequestHandler: jest.fn() }))`, `apiHandler` object with `get: jest.fn()` etc.). Call `(ApiRequestHandler as jest.Mock).mockImplementation(() => apiHandler)` **before** constructing `new AnalyticsService({ apiDomain, token })` (llm.test.ts does it in the other order; do not copy that). Tests, asserting `apiHandler.get` toHaveBeenCalledWith(path, params):
  - `getAssistantsChats` / `getWorkflows` with `attributes: { team: "alpha" }` -> params `attributes` is the string `'{"team":"alpha"}'`.
  - round-trip of a quote/non-ASCII value via `JSON.parse(params.attributes)`.
  - omitted attributes -> `"attributes" in params` is false; defaults `page: 0`, `per_page: 20` present.
  - `attributes: {}` -> `"{}"`.
  - `getAssistantsRequests` -> path `/v1/analytics/assistants-requests`, `client_source`, `assistant_id`, JSON attributes.
  - `getWorkflowsExecutions` -> path `/v1/analytics/workflows-executions`.
  - `getAttributesUsage({ attribute_key: "team", attributes: {...} })` -> path `/v1/analytics/attributes-usage`; `await expect(service.getAttributesUsage({} as any)).rejects.toThrow()` (ZodError).
  - `getToolsUsage({ attributes: {team:"alpha"} } as any)` -> params contain no `attributes` key (zod strips it).
- [ ] **Step 2: Run to verify failure**: `cd sdk/codemie-nodejs && npx jest tests/unit/services/analytics.test.ts` -> FAIL.
- [ ] **Step 3: Implement schemas** as above in `schemas/analytics.ts`.
- [ ] **Step 4: Implement service**: module-private `toQueryParams<T extends { attributes?: Record<string, string> }>(params: T)` that returns the params with `attributes` replaced by `JSON.stringify(attributes)` when defined, and without the key otherwise. Every attributes-capable method does `Schema.parse(_params)` -> `toQueryParams` -> `this.api.get<TabularResponse>(path, queryParams)`. This is required because axios would send `attributes[team]=alpha` for an object.
- [ ] **Step 5: Verify**: `npx jest tests/unit/services/analytics.test.ts` PASS; `npm run lint` and `npx tsc --noEmit` clean.

Test-first: yes — `getAssistantsChats` attributes test fails because the schema strips unknown `attributes` today (called without the key).

---

### Task 3: Python body and response models

**Files:**
- Modify: `sdk/codemie-python/src/codemie_sdk/models/assistant.py` (`AssistantChatRequest`, line 468; append a field after `mcp_server_single_usage`, line ~508)
- Modify: `sdk/codemie-python/src/codemie_sdk/models/workflow_execution_payload.py` (`WorkflowExecutionCreateRequest`, after `tags`)
- Modify: `sdk/codemie-python/src/codemie_sdk/services/workflow_execution.py` (`create`, line 49-89)
- Modify: `sdk/codemie-python/src/codemie_sdk/models/conversation.py` (`ConversationDetails`, line 161)
- Modify: `sdk/codemie-python/src/codemie_sdk/models/workflow.py` (`WorkflowExecution`, line 80)
- Test: `sdk/codemie-python/tests/test_run_attributes_models.py` (create)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `attributes: dict[str, str] | None = None` (with a description mentioning run attributes, immutable per conversation, ignored when `save_history=false` for chat) on `AssistantChatRequest`, `WorkflowExecutionCreateRequest`, `ConversationDetails`, `WorkflowExecution`. `WorkflowExecutionService.create(..., file_names=None, attributes: dict[str, str] | None = None)` — new kwarg appended last so positional callers keep working; passed into the payload. No key/value validation.

- [ ] **Step 1: Write failing tests** in `tests/test_run_attributes_models.py`:
  - `test_chat_request_dumps_attributes_dict`: `AssistantChatRequest(text="hi", attributes={"team": "alpha"}).model_dump(exclude_none=True, by_alias=True)["attributes"] == {"team": "alpha"}` (a dict, not a string); omitted -> key absent.
  - `test_workflow_execution_create_sends_attributes_in_body`: `WorkflowExecutionService("https://api.example.com", "token", "wf1").create(user_input="x", attributes={"team": "alpha"})` with `patch("codemie_sdk.utils.http.requests.post")` returning `_ok_response({})` (copy helper from `tests/test_analytics_cli_analytics.py:7`); assert `post.call_args.kwargs["json"]["attributes"] == {"team": "alpha"}`. Check the service constructor signature in `services/workflow_execution.py` before writing the test.
  - `test_conversation_details_parses_attributes_and_absent`: build `ConversationDetails` from a minimal valid dict (copy required fields from the model, lines 164-188) with and without `attributes` (also `None`); expect `{"team": "alpha"}` / `None`.
  - `test_workflow_execution_response_parses_attributes_and_absent`: `WorkflowExecution.model_validate` with aliases `overall_status`, `date`, `update_date`, a `created_by` user (see `User` in `models/workflow.py`) with/without `attributes`.
- [ ] **Step 2: Run to verify failure**: `cd sdk/codemie-python && python -m pytest tests/test_run_attributes_models.py -v` -> FAIL.
- [ ] **Step 3: Implement** the four model fields and the `create` kwarg/docstring line.
- [ ] **Step 4: Verify**: `python -m pytest tests/test_run_attributes_models.py tests/test_chat_with_version.py tests/test_assistant_versions.py -v` PASS; `ruff check src tests && ruff format --check src tests` clean.

Test-first: yes — `test_chat_request_dumps_attributes_dict` fails because pydantic drops/rejects the unknown `attributes` field today.

---

### Task 4: Node body and response types

**Files:**
- Modify: `sdk/codemie-nodejs/src/schemas/assistant.ts` (`AssistantChatParamsSchema`, line 123; add after `save_history`, line 148)
- Modify: `sdk/codemie-nodejs/src/schemas/workflow.ts` (`WorkflowExecutionCreateParamsSchema`, line 77; add after `tags`)
- Modify: `sdk/codemie-nodejs/src/services/workflow_execution.ts` (`create`, line 43-59)
- Modify: `sdk/codemie-nodejs/src/models/workflow.ts` (`WorkflowExecutionResponse` line 77, `WorkflowExecution` line 99)
- Modify: `sdk/codemie-nodejs/src/mappers/workflow.mapper.ts` (`mapWorkflowExecutionResponse`, line 26)
- Modify: `sdk/codemie-nodejs/src/models/conversation.ts` (`ConversationDetails`, line 102)
- Test (extend existing): `tests/unit/schemas/assistant.schema.test.ts`, `tests/unit/services/workflow_execution.test.ts`, `tests/unit/mappers/workflow.mapper.test.ts`, `tests/unit/services/conversation.test.ts`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `attributes: z.record(z.string(), z.string()).optional()` on the two create schemas (so it survives `.parse`; VirtualAssistant schema is intentionally untouched); `attributes?: Record<string, string> | null` on `WorkflowExecutionResponse`, `WorkflowExecution` and `ConversationDetails`; `WorkflowExecutionService.create(userInput?, fileName?, sessionId?, propagateHeaders?, headers?, tags?, attributes?: Record<string, string>)` — appended last so existing callers are unaffected; `mapWorkflowExecutionResponse` copies `attributes` through (the existing `omitUndefined` drops it when absent; keep `null` as-is).

- [ ] **Step 1: Write failing tests** by adding cases to the existing files, following each file's existing style:
  - `assistant.schema.test.ts`: `AssistantChatParamsSchema.parse({ text: "hi", history: [], attributes: { team: "alpha" } })` keeps `attributes` equal to `{ team: "alpha" }` (an object, not a string); absent stays absent.
  - `workflow_execution.test.ts`: `create("x", undefined, undefined, undefined, undefined, undefined, { team: "alpha" })` -> `apiHandler.post` called with a body containing `attributes: { team: "alpha" }`; without it, body has no `attributes`.
  - `workflow.mapper.test.ts`: response with `attributes: { team: "alpha" }` maps to the same; response without it maps with no `attributes` key.
  - `conversation.test.ts`: a `getById`-style response including `attributes` is returned unchanged (type-level check via assigning to `ConversationDetails`; use the file's existing get-details test as the template).
- [ ] **Step 2: Run to verify failure**: `cd sdk/codemie-nodejs && npx jest tests/unit/schemas/assistant.schema.test.ts tests/unit/services/workflow_execution.test.ts tests/unit/mappers/workflow.mapper.test.ts tests/unit/services/conversation.test.ts` -> FAIL (zod strips `attributes`; TS error on unknown property).
- [ ] **Step 3: Implement** schema fields, interface fields, mapper passthrough and the `create` parameter (forward as `attributes` in the schema parse input).
- [ ] **Step 4: Verify**: the same jest command PASS, then `npm test` (unit suite), `npm run lint`, `npx tsc --noEmit` clean.

Test-first: yes — the `AssistantChatParamsSchema` test fails because zod strips the unlisted `attributes` key on parse today.

---

## Self-review notes

- Negative-constraint pass: do-not-widen shared paginated class -> Tasks 1 and 2 add dedicated subclasses and assert no `attributes` on `getToolsUsage` / paginated model; do-not-touch `last_90_days` -> Global Constraints, no task edits that line; no over-validation -> Global Constraints, no task adds key/value checks; no README/CHANGELOG -> none touched; do-not-commit -> header says implementer commits per task, no commit blocks. No task violates these.
- Coverage: requirement 1 -> Tasks 1, 2; 2 -> Tasks 1, 2 (attribute_key decision in Global Constraints); 3 -> Tasks 3, 4; 4 -> serialization tests in Tasks 1, 2; 5 -> Tasks 1, 2 and exports.
