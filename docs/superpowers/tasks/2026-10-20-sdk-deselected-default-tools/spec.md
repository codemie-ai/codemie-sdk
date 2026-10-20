# Spec: SDKs carry `deselected_default_tools`

**Size**: M (18/36). **Scope**: Python SDK and Node SDK only. **Story**: `.story-artifacts/story.md`.

## Intent

The backend adds a per-assistant opt-out list of default datasource tools. If the SDK models drop it, an SDK update could silently re-enable a deselected tool. This change makes both SDKs send and return the field and otherwise leaves existing behavior untouched.

## Backend contract (source: backend repo `rest_api/models/assistant.py`, backend spec)

- Field `deselected_default_tools: list[str]`, snake_case on the wire, backend default `[]`.
- Backend-valid values: `get_repository_file_tree`, `search_code_repo`, `search_kb`. The SDKs do not check this; the backend rejects others at save time and the error surfaces to the caller (D8).
- An omitted field leaves the stored value unchanged on update (D10).

## Behavior

- **Read models** (Python `Assistant` and any version/read model that carries `toolkits`; Node `Assistant`, `AssistantVersion`): the field is a string list that defaults to `[]` when the backend omits it, so older backends and payloads keep working (D9).
- **Request models** (Python `AssistantRequestBase` and so create/update; Node create/update request types and their zod schemas in `src/schemas/assistant.ts`): the field is optional with no default (`None` / `undefined`). Python's existing `model_dump(exclude_none=True)` omits it when unset. Node must not add it to the payload when `undefined`. An explicit `[]` counts as set, is sent, and clears the deselection.
- **Node mapper** (`src/mappers/assistant.mapper.ts`): passes the field through in both directions, so it is not stripped on create, update or read.
- **Python `extra="ignore"`**: the field is declared explicitly so it is no longer dropped.
- **No client-side validation** of names or variant conflicts. Backend errors propagate through the existing exception paths unchanged.
- **Tool listing** (`get_tools` / Node equivalent): no code change. The backend now lists the default tools, and the SDK already returns toolkits as given.
- Python: where the service rebuilds a request from an existing assistant or version (`services/assistant.py` around l.319), carry the field only if that code already copies `toolkits`, so a version restore does not lose it.
- Docs: add the field to the assistant sections of each SDK README that list assistant fields.

## Acceptance criteria

1. Python create with the field set sends it, and the returned `Assistant` exposes it.
2. Python update with a changed list sends it, and the returned `Assistant` exposes it.
3. Python request without the field omits the key from the payload on create and update. A read without the field yields `[]`.
4. Node create, update and read behave as 1-3 (schema accepts it, mapper preserves it, key absent when `undefined`).
5. An explicit `[]` is sent in both SDKs.
6. A backend rejection (for example an unknown tool name) surfaces as the SDK's existing error type in both SDKs, and nothing swallows it.
7. A tool listing containing default datasource tools is returned unchanged (regression test).

## Tests

- Python: extend `sdk/codemie-python/tests` with payload-shape tests (mocked HTTP) and read-model parsing.
- Node: extend `tests/unit/services/assistant.test.ts` and `tests/unit/schemas/assistant.schema.test.ts`.
- E2E and test-harness changes are out of scope.

## Non-goals

- IaC Node tooling: backup/import round-trip and checksum difference criteria are tracked in the repo that owns the IaC package. That package is not in this repo.
- Client-side validation of tool names or standard/V2 variant conflicts.
- Backend or UI behavior.
- New SDK methods unrelated to this field.
- Changes to provider, Git or MCP tool handling.
- E2E specs against a live backend.

## Open risks

- Field name and shape were taken from the sibling backend checkout, not from a published API contract. Confirm if the backend changes.
- Whether the backend treats an omitted field as unchanged on update (D10) is a backend guarantee the SDK tests cannot verify.
