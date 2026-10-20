# SDK deselected_default_tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox syntax.

**Goal:** Python and Node SDKs send and return the assistant-level `deselected_default_tools: list[str]` field.

**Architecture:** Add the field to read models (default `[]`) and request models (optional, no default, omitted when unset). No client-side validation; backend errors propagate unchanged.

**Tech Stack:** Python (pydantic, pytest, mocked HTTP), TypeScript (zod, vitest/jest as already used in `tests/unit`).

**Spec:** `/Users/vladimir_sesum1/codemie-dev/codemie-sdk/docs/superpowers/tasks/2026-10-20-sdk-deselected-default-tools/spec.md`

Commit per task using the repository's existing convention.

## Global Constraints

- Wire name `deselected_default_tools`, snake_case, values are plain strings (backend validates: `get_repository_file_tree`, `search_code_repo`, `search_kb`).
- Request side: unset means key absent; explicit `[]` is sent. No name or variant validation in the SDK.
- IaC, E2E and test-harness are out of scope. `get_tools` needs no code change.

## Review Focus

- Omitted field on update must not send `[]` (would clear the deselection): tested in Tasks 1 and 2.
- Version-restore fallback in Python must not lose the field: Task 1.
- Backend HTTP error on a bad tool name must not be swallowed: Tasks 1 and 2.

---

### Task 1: Python SDK

**Files:**
- Modify: `sdk/codemie-python/src/codemie_sdk/models/assistant.py` (`Assistant` ~l.222-274, `AssistantRequestBase` ~l.277-310, `AssistantVersion` ~l.411-430)
- Modify: `sdk/codemie-python/src/codemie_sdk/services/assistant.py:319-321` (rollback fallback `AssistantUpdateRequest`)
- Modify: `sdk/codemie-python/README.md` (assistant fields section)
- Test: `sdk/codemie-python/tests/test_assistant_deselected_default_tools.py` (new; follow mocking style of `tests/test_assistant_versions.py`)

**Interfaces:**
- Produces: `Assistant.deselected_default_tools: list[str]` and `AssistantVersion.deselected_default_tools: list[str]` (both `Field(default_factory=list)`); `AssistantRequestBase.deselected_default_tools: list[str] | None = None`.

- [ ] **Step 1: Write failing tests** (mock the API client, inspect `json_data` passed by `AssistantService.create`/`update`):
  - `test_create_sends_field_when_set` — payload `["search_kb"]`; assert `json_data["deselected_default_tools"] == ["search_kb"]`.
  - `test_update_sends_changed_list`.
  - `test_unset_field_omitted_from_payload` — create and update; assert key not in `json_data`.
  - `test_explicit_empty_list_is_sent` — `[]` present in payload.
  - `test_read_models_expose_field_and_default_empty` — `Assistant` and `AssistantVersion` parsed with and without the key (`[]` when absent, value when present).
  - `test_backend_rejection_propagates` — mocked request raises `requests.HTTPError`; `create` re-raises the same error type.
  - `test_get_tools_returns_default_datasource_toolkit_unchanged` — mocked listing containing `search_kb`/`search_code_repo`/`get_repository_file_tree` tools is returned as parsed `ToolKitDetails` with those tool names intact.
  - `test_rollback_fallback_carries_field` — in the HTTPError fallback path (service l.299-342) the built `AssistantUpdateRequest` has the version's `deselected_default_tools`.
- [ ] **Step 2: Run** `cd sdk/codemie-python && pytest tests/test_assistant_deselected_default_tools.py -v`. Expected: field tests FAIL (the propagation and listing tests may already pass).
- [ ] **Step 3: Implement** the three model fields above, and add `deselected_default_tools=version.deselected_default_tools if hasattr(version, "deselected_default_tools") else assistant.deselected_default_tools` after `toolkits=` in the fallback, matching its existing style.
- [ ] **Step 4: Document** the field in the README assistant fields list (one line: list of default datasource tool names opted out; omit to leave unchanged on update).
- [ ] **Step 5: Run** the new test file plus `pytest tests/test_assistant_versions.py -v`. Expected: PASS.

### Task 2: Node SDK

**Files:**
- Modify: `sdk/codemie-nodejs/src/schemas/assistant.ts:47-115` (add `deselected_default_tools: z.array(z.string()).optional()` to `AssistantCreateParamsSchema`; update schema aliases it)
- Modify: `sdk/codemie-nodejs/src/models/assistant.ts` (`Assistant` l.98-125, `AssistantVersion` l.161-178: add `deselected_default_tools: string[]`)
- Modify: `sdk/codemie-nodejs/src/services/assistant.ts:86-100, 195` (`get`, `getBySlug`, `getVersion`: return the payload with `deselected_default_tools` defaulted to `[]` when absent)
- Modify: `sdk/codemie-nodejs/README.md` (assistant fields section)
- Test: `sdk/codemie-nodejs/tests/unit/schemas/assistant.schema.test.ts`, `sdk/codemie-nodejs/tests/unit/services/assistant.test.ts`, `sdk/codemie-nodejs/tests/unit/services/assistant.versions.test.ts`

**Interfaces:**
- Produces: `Assistant.deselected_default_tools: string[]`, `AssistantVersion.deselected_default_tools: string[]`; create/update params accept optional `deselected_default_tools?: string[]`. `AssistantMapper` (chat-response only) needs no change: create/update/read do not pass through it.

- [ ] **Step 1: Write failing tests**, reusing existing fixtures/mocks in those files (existing fixtures at `assistant.test.ts:41,184,275` and `assistant.versions.test.ts:40,63` need `deselected_default_tools: []` once the type is required):
  - schema: accepts `["search_kb"]`; accepts `[]`; parsed output has no `deselected_default_tools` key when input omits it; rejects non-string items.
  - service `create`/`update`: body sent to the HTTP mock contains the list when set, `[]` when explicit `[]`, and no key when undefined.
  - service `get`, `getBySlug`, `getVersion`: response lacking the key yields `[]`; response with the key returns it.
  - a rejected HTTP call on `create` rejects with the same error object (not swallowed).
  - `getTools` regression: listing with default datasource tools returned unchanged (add to the existing tools test if one exists in `assistant.test.ts`).
- [ ] **Step 2: Run** the three unit test files with the package's test script (see `package.json`). Expected: new tests FAIL.
- [ ] **Step 3: Implement** the schema field, the two interface fields, and the `?? []` defaulting in the three service read methods.
- [ ] **Step 4: Document** the field in the README assistant section, same wording as Task 1.
- [ ] **Step 5: Run** the three files plus `tsc --noEmit` via the package's typecheck script. Expected: PASS, no type errors.

negative-constraints: honored. "No client-side validation" (Tasks 1, 2 add no name checks); "omitted field must not clear" (unset-omitted tests); IaC/E2E/harness non-goals (no task touches them); "no changes to get_tools" (regression tests only); "mapper pass-through" satisfied trivially since create/update/read bypass it.
