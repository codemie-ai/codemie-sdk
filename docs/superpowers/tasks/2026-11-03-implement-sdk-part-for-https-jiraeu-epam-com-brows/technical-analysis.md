# Technical Research

**Task**: analytics attributes endpoints sdk
**Generated**: 2026-11-03
**Research path**: filesystem

---

## 1. Original Context

Implement SDK part for https://jiraeu.epam.com/browse/EPMCDME-16484. Review what API changes were done in the codemie repo (sibling) and update the SDK accordingly. Make sure attributes request parameter is added to already existing API endpoints and 3 new analytic endpoints are created as well. Change should be done for both SDK

---

## 2. Codebase Findings

Backend source of truth: `/Users/bohdan_maliar/Projects/codemie-dev/codemie`, branch `EPMCDME-16484_run-attributes` (19 commits ahead of `main`, unmerged; merge-base `d2d59a21e6`). Working tree has only unrelated config modifications. Jira unreachable.

### Existing Implementations

**Purpose A: filter existing analytics tables by run attributes (query param `attributes`)**
- Backend, existing endpoints that gained it (all `GET`, `str | None = Query(None)`, default none):
  - `/v1/analytics/assistants-chats` — `routers/analytics/usage.py:~142` (before it already had `client_source`)
  - `/v1/analytics/workflows` — `usage.py:~240`
- Value is a **JSON-encoded string**, not a dict: `{"team": "alpha"}`. Parsed by `core/run_attributes.py::parse_attributes_filter`; invalid -> HTTP 422 "Invalid attributes filter". Empty/blank string = no filter. AND semantics (all pairs must match), exact key=value term match (`query_builder.py::add_attributes_filter`).
- Attribute rules (`core/run_attributes.py`): key `^[a-z0-9][a-z0-9._-]{0,62}[a-z0-9]$` (2-64 chars, lowercase letters/digits/`.`/`_`/`-`), must not start with `codemie.` or `otel.`; value 1-128 UTF-16 code units, string, no control chars/unpaired surrogates; max keys `config.RUN_ATTRIBUTES_MAX_KEYS = 4` (`configs/config.py`, env-configurable). Filter is validated with the same rules as run attributes.
- Filters to which `attributes` was NOT added (backend, verified by grep of `routers/analytics/*.py`): `summaries` and all other analytics routes. Commit `6cdc72513f` explicitly removed an attribute-keys endpoint and the filter on summaries.

**Purpose B: three new analytics endpoints** (all `GET`, response `TabularResponse`, auth + standard analytics scoping, share `AnalyticsQueryParams`: `time_period`, `start_date`, `end_date`, `users`, `projects`, `page` (>=0, default 0), `per_page` (1-1000, default `ANALYTICS_DEFAULT_PAGE_SIZE`) — `_common.py:154`):
1. `/v1/analytics/assistants-requests` (`usage.py` `get_assistants_requests`) — one row per assistant request, newest first. Extra params: `client_source` (enum `ClientSource`), `assistant_id` (exact id, `str`), `attributes`. Columns: request_id, timestamp, conversation_id, assistant_id, assistant_name, user_id, user_name, user_email, project, llm_model, client_source, input_tokens, output_tokens, total_tokens, cache_read_input_tokens, money_spent, cached_tokens_money_spent, execution_time, status, attributes (`assistant_handler.py::_get_assistants_requests_columns`). `total_count` capped at 10,000 by Elasticsearch.
2. `/v1/analytics/workflows-executions` (`get_workflows_executions`) — one row per `execution_id`, most recent activity first. Extra params: `client_source`, `attributes`. Columns: execution_id, last_activity, workflow_name, status, user_id, user_name, user_email, project, usage_records, input_tokens, output_tokens, total_tokens, money_spent, execution_time, attributes (`workflow_handler.py::_get_workflows_executions_columns`). `totals` carries input_tokens/output_tokens/money_spent sums; `total_count` approximate above 3,000; 503 "Incomplete workflow analytics" possible.
3. `/v1/analytics/attributes-usage` (`get_attributes_usage`) — usage per value of one attribute key. Params: **`attribute_key` (required in practice: declared `str | None`, missing/invalid -> 422 "Invalid attribute key")**, `client_source`, `attributes` (narrowing filter), plus the common ones. Columns: value, conversations, workflow_executions, total_tokens, total_cost, unique_users, last_used (`attributes_handler.py`). Unknown key -> empty table.
- Row-level `attributes` cell is `{key: value}` dict or `null`; column type is `"json"` (new column type; `ColumnDefinition.type` is a free `str` in both SDKs, description lists only string/number/date).
- Response envelope for all three is the existing `TabularResponse` (`rest_api/models/analytics.py:115`: `data{columns,rows,totals}`, `metadata`, `pagination`, plus optional `fixed_timeframe`). No new response model in the backend.

**Purpose C (adjacent, same ticket): setting attributes when starting runs** — body field `attributes: dict[str, str] | None` added to `AssistantChatRequest` (`core/models.py:726`) and `CreateWorkflowExecutionRequest` (`workflow_execution.py:350`); response field `attributes` added to `ConversationResponse`, `WorkflowExecutionResponse`, and the `Conversation`/`WorkflowExecution` tables. Same validation rules; immutability per conversation (422 if changed after history exists); ignored when `save_history=false`. The task text speaks only of the analytics endpoints; whether these body/response fields are in scope is not stated.

**SDK today (both SDKs)** — what serves analytics:
- Python: `sdk/codemie-python/src/codemie_sdk/services/analytics.py` `AnalyticsService` (703 lines); `get_assistants_chats` (line 75) and `get_workflows` (95) take `PaginatedAnalyticsQueryParams | None`, call `self._api.get("/v1/analytics/...", TabularResponse, params=params.model_dump(exclude_none=True), wrap_response=False)`. Models: `models/analytics.py` — `AnalyticsQueryParams` (time_period, start_date, end_date, users, projects; `extra="ignore"`), `PaginatedAnalyticsQueryParams` (+page=0, per_page=20), `TabularResponse/TabularData/ColumnDefinition/PaginationMetadata/ResponseMetadata`. Exports in `codemie_sdk/__init__.py` (imports lines ~84-104, `__all__` ~266-275; `PaginatedAnalyticsQueryParams` already exported; `TabularResponse` import to be confirmed by planner). Client wiring `client/client.py:111` (`self.analytics`). Tests: `tests/test_analytics_cli_analytics.py` (pytest, `MagicMock` response + `patch("codemie_sdk.utils.http.requests.post")`, asserts URL/headers/params), `tests/test_project_cli_analytics.py`. Docs: README has no analytics section.
- Node: `sdk/codemie-nodejs/src/services/analytics.ts` `AnalyticsService` (143 lines); `getAssistantsChats`/`getWorkflows` parse `PaginatedAnalyticsQueryParamsSchema` then `this.api.get<TabularResponse>(path, params)`. Schemas: `src/schemas/analytics.ts` (zod 4, `z.object({...}).readonly()`, so unknown keys are stripped on parse). Types: `src/models/analytics.ts` (interfaces; `TabularResponse` has no `fixed_timeframe`). Barrel exports `src/models/index.ts`, `src/schemas/index.ts`, `src/services/index.ts` use `export *`. Client getter `client/client.ts:136`. Tests: **no analytics test files** in `tests/unit/{services,schemas,models}`; style reference `tests/unit/services/llm.test.ts` (jest, `jest.mock("../../../src/utils/http")` with `ApiRequestHandler` mocked). README has no analytics section.
- Neither SDK has any `attributes` filter, `client_source`, `assistant_id`, or the three new endpoints today (grep of both `src` trees).

**Other touched code**: `utils/http.py::ApiRequestHandler.get` (Python, passes `params` straight to `requests.get`); `utils/http.ts::ApiRequestHandler.get(path, params)` (Node, passes to axios `params`).

### Decisions Already in the Code

- Backend carries the filter as a JSON **string** query param (`usage.py`, `_common.py:ATTRIBUTES_FILTER_DESC`); alternative (repeated `attributes[k]=v` params) not used; reason: none recorded beyond the description. SDK params are dicts in the model layer today only for non-query data; `requests` would serialise a dict value as bare keys and axios as `attributes[team]=alpha`, neither of which the backend parses (stored dict -> must be sent as JSON text; this is a fact about the transports, the choice of where to encode is for the spec).
- Convention (both SDKs): one method per endpoint, typed params object, generic `TabularResponse` for every tabular endpoint, rows are `dict[str, Any]` / `Record<string, unknown>` (no per-endpoint row models). Python: `params.model_dump(exclude_none=True)`, `wrap_response=False`. Node: `Schema.parse(_params)` then `api.get`.
- Method naming convention: Python snake_case `get_<endpoint_with_underscores>`; Node camelCase `get<EndpointPascal>`.
- Paginated defaults in SDK: page 0, per_page 20 (Python model default and Node zod default). Backend default per_page comes from `ANALYTICS_DEFAULT_PAGE_SIZE` and max 1000; SDK does not enforce max.
- Backend `client_source` param exists on the existing endpoints (pre-branch) but the SDKs omit it; the SDK convention so far is to not mirror every backend param. New endpoints take `client_source`/`assistant_id` too.
- Versioning: manifests hold base `0.1.0`; version is stamped from release tag at publish (`docs/RELEASING.md` lines 21-28). No CHANGELOG in the SDK repo. Recent SDK feature commits (`d042a6c`, `f81adf7`) touched only src + tests, no version/changelog/README, commit style `feat(python): ...`/`fix(python): ...`.

### Task Statements Checked Against the Code

- "attributes request parameter is added to already existing API endpoints" — holds in backend for exactly two existing endpoints, `assistants-chats` and `workflows` (`usage.py`). Contradicted if read as "all existing analytics endpoints": `summaries` etc. have no such param. Ambiguity: could also refer to the chat / workflow-execution **body** field `attributes` (Purpose C); unverified which is meant (Jira unreachable).
- "3 new analytic endpoints" — holds: `assistants-requests`, `workflows-executions`, `attributes-usage` (backend-added; a fourth, an attribute-keys listing, was added then removed in `6cdc72513f`, so it is not in the final branch).
- "Change should be done for both SDK" — holds: both `sdk/codemie-python` and `sdk/codemie-nodejs` have `AnalyticsService` with the sibling method pairs.
- "Review what API changes were done in the codemie repo" — backend changes are on an **unmerged branch**; the openapi baseline `tests/codemie/rest_api/router_guards/baselines/openapi.json` on that branch contains the three paths and may still change before merge. Backend spec lists "Any UI or SDK change" as a non-goal (`docs/superpowers/tasks/2026-10-30-epmcdme-16484-run-attributes/spec.md:57`).

### Consumers of Changed Contracts

- `PaginatedAnalyticsQueryParams` (Python `models/analytics.py`) is subclassed/used by `AnalyticsService` methods get_assistants_chats, get_workflows, get_tools_usage, get_webhooks_invocation, mcp/spend/budget/activity/agents/cli-* getters (about 19 tabular endpoints, `services/analytics.py` lines 75-450); also exported at `__init__.py:97,267`. Adding a field to this shared class would be accepted by all of them, but backend honours `attributes` only on the two endpoints above plus the three new ones. `CliAnalyticsQueryParams` / `CliAnalyticsSessionsQueryParams` extend `AnalyticsQueryParams`, not the paginated one.
- Node `PaginatedAnalyticsQueryParamsSchema` / `analyticsQueryParamsBase` (`schemas/analytics.ts`) is used by the same set of Node methods; `AnalyticsQueryParamsSchema` by getSummaries/getCliSummary/getUsers.
- `TabularResponse`/`ColumnDefinition` consumers: all tabular methods in both SDKs; no change to the shape is made by the backend branch.
- Python `ApiRequestHandler.get` / Node `ApiRequestHandler.get` consume `params` generically; no other caller sends dict-valued query params.
- Any code outside the SDK repo (CLI/UI) that uses these services: not searched.

### Architecture and Layers Affected

Python: models (`models/analytics.py`) -> service (`services/analytics.py`) -> exports (`__init__.py`) -> tests. Node: schemas (`schemas/analytics.ts`) -> service (`services/analytics.ts`) -> (types `models/analytics.ts` if new types are added) -> tests. No client-wiring change (analytics service already registered).

### Integration Points

HTTP only: `GET /v1/analytics/{assistants-chats,workflows,assistants-requests,workflows-executions,attributes-usage}` through each SDK's `ApiRequestHandler`. No DB/config.

### Patterns and Conventions

See Decisions. Python formatting is black-style wrapped at 88 cols with ruff (Makefile in `sdk/codemie-python`); Node uses Biome (`npm run lint`, `format`) and `tsup` build.

---

## 3. Documentation Findings

### Guides and Architecture Docs
No `.ai-run/guides/` in this repo (conventions derived from code). `docs/RELEASING.md` covers release only. SDK READMEs contain no analytics section.

### Architectural Decisions
Backend-side: `codemie/docs/superpowers/tasks/2026-10-30-epmcdme-16484-run-attributes/{spec.md,plan.md}` (SDK listed as non-goal; describes immutable-attributes semantics and endpoint trust notes). Nothing recorded SDK-side.

### Derived Conventions
As in Section 2. Commit scope prefixes `feat(python)`/`fix(python)` indicate per-SDK commits.

---

## 4. Testing Landscape

### Existing Coverage
Python: `tests/test_analytics_cli_analytics.py` (cli-analytics hook ingestion; mocks `requests`), no tests for `get_assistants_chats`/`get_workflows`. Node: zero analytics tests.

### Testing Framework and Patterns
Python: pytest (`pytest.ini`), `unittest.mock.patch("codemie_sdk.utils.http.requests.get|post")` + `MagicMock` JSON response. Node: jest 29 + ts-jest, module mocking of `utils/http`, tests under `tests/unit/{services,schemas,models}`; e2e under `tests/e2e/specs` (needs live stack).

### Coverage Gaps
No tests anywhere for tabular analytics getters; no test for dict-to-query serialisation; Node has no analytics spec at all.

---

## 5. Configuration and Environment

### Environment Variables
None in SDK for this feature. Backend: `RUN_ATTRIBUTES_MAX_KEYS` (default 4).

### Configuration Files
`sdk/codemie-python/pyproject.toml` (version base 0.1.0), `sdk/codemie-nodejs/package.json` (0.1.0, axios 1.15.0, zod 4.3.5).

### Feature Flags and Deployment Concerns
No feature flag found for run attributes in the backend router code. Release is by GitHub Release tag per package.

---

## 6. Risk Indicators

- Backend work is on an unmerged branch; endpoint contracts could change before release (openapi baseline on branch is the only frozen artifact).
- `attributes` is a JSON string in the query; both SDK transports serialise dict values differently (Python `requests` -> keys only, axios -> bracket notation). Speculative: SDK must encode explicitly; untested in both SDKs today.
- `attributes-usage` `attribute_key` is optional in OpenAPI (`str | None`) but 422 when missing; spec must decide required vs optional (backend fact: required in behaviour).
- Shared `PaginatedAnalyticsQueryParams` / `PaginatedAnalyticsQueryParamsSchema` feed ~19 endpoints; backend honours `attributes` on only 5 (see Consumers). Node zod `.readonly()` object strips unknown keys, so an unlisted param is silently dropped.
- SDKs lack `client_source` (backend has it on all five relevant endpoints) and `assistant_id`; parity gap, not mentioned by task.
- Column type `"json"` and `TabularResponse.fixed_timeframe` exist in backend but not in SDK type descriptions.
- Node `time_period` enum contains `last_60_days`, Python description lists `last_90_days`; backend `time_parser.py` has `last_60_days`. Pre-existing doc mismatch in Python, unrelated.
- Purpose C (body `attributes` on chat / workflow-execution, response `attributes`) may or may not be in scope; adds model changes in `models/assistant.py:468`, `models/workflow_execution_payload.py`, `models/conversation.py`, `models/workflow.py` (Python) and Node counterparts if included.
- No existing Node analytics tests; test harness for it has to be created from the llm.test.ts pattern.
- No CHANGELOG/README analytics docs to update; docs impact is nil unless planner chooses to add.

---

## 7. Summary for Complexity Assessment

The change is confined to the analytics slice of two SDKs: models/schema (add an `attributes` filter and optional new param types), five service methods (two modified, three new), export surface (Python `__init__`, Node barrel already `export *`), and tests. The backend API is fully defined on an unmerged sibling branch: two existing endpoints (`assistants-chats`, `workflows`) gain `attributes`; three endpoints are new (`assistants-requests`, `workflows-executions`, `attributes-usage`), all returning the existing generic `TabularResponse`, so no new response models are forced. Roughly 4-6 source files per SDK plus new test files.

Technical novelty is low (copy existing getter pattern), with one real wrinkle: `attributes` must travel as a JSON string while SDK users naturally hold a dict, and the two HTTP stacks would otherwise mangle a dict. A second design ambiguity is whether to add dedicated param classes for the new endpoints (extra params `client_source`, `assistant_id`, `attribute_key`) or reuse the shared paginated ones.

Test posture is thin: Python has pytest mock patterns for analytics (cli only), Node has none for analytics. Main risks are the unmerged backend contract, scope ambiguity of Purpose C (body attributes on run creation), and the shared param class used by ~19 other endpoints.

---

## 8. External References

None named by the task (Jira ticket EPMCDME-16484 could not be fetched; the sibling backend repo was used as source of truth as instructed: `/Users/bohdan_maliar/Projects/codemie-dev/codemie`, branch `EPMCDME-16484_run-attributes`, key files `src/codemie/rest_api/routers/analytics/usage.py`, `_common.py`, `src/codemie/core/run_attributes.py`, `src/codemie/service/analytics/handlers/{assistant,workflow,attributes}_handler.py`).
