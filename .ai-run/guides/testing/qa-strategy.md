# QA Strategy

**Last assessed**: 2026-11-12

How this repository tests its two SDKs. For the exact commands see `.ai-run/guides/quality-gates.md`; this file repeats only the test commands, in the same form.

## Test Frameworks

| Framework | Type | Config file | Test directories |
|---|---|---|---|
| pytest (with `pytest-cov`) | unit | `sdk/codemie-python/pytest.ini` | `sdk/codemie-python/tests/` |
| Jest with `ts-jest` | unit | `sdk/codemie-nodejs/jest.config.mjs` | `sdk/codemie-nodejs/tests/unit/` |
| Jest with `ts-jest` | e2e (live platform) | `sdk/codemie-nodejs/jest.e2e.config.mjs` | `sdk/codemie-nodejs/tests/e2e/specs/` |

## Test Types in Use

### Unit Tests

Python SDK:
- **Location**: `sdk/codemie-python/tests/` (flat, one `test_<area>.py` per area)
- **Pattern**: `test_<area>.py`. Most files use plain `def test_*()` functions. Some files group tests in `class Test<Thing>` (for example `test_workflow_definition.py`, `test_user_lifecycle_service.py`). Follow the style of the file you extend.
- **Run command**: `poetry run pytest tests/` (from `sdk/codemie-python`; CI job `python`, `.github/workflows/ci.yml`)
- **Example**: `sdk/codemie-python/tests/test_credentials.py:32` (`test_external_token_wins_over_password_grant`)

Node.js SDK:
- **Location**: `sdk/codemie-nodejs/tests/unit/`, one subdirectory per source layer (`auth/`, `client/`, `exceptions/`, `mappers/`, `models/`, `schemas/`, `services/`, `utils/`)
- **Pattern**: `<area>.test.ts` (`testMatch: ['**/*.test.ts']` in `jest.config.mjs`)
- **Run command**: `npm test` (from `sdk/codemie-nodejs`; CI job `node`, `.github/workflows/ci.yml`)
- **Example**: `sdk/codemie-nodejs/tests/unit/services/assistant.versions.test.ts:33` (`listVersions should call correct endpoint and return array`)

### Integration Tests
- **Location**: none detected. No test in this repository calls a real HTTP server from CI.
- **Pattern**: n/a
- **Run command**: n/a

### End-to-End Tests

Node.js SDK e2e suite:
- **Location**: `sdk/codemie-nodejs/tests/e2e/specs/` (for example `assistant.spec.ts`, `workflow.spec.ts`, `datasource_with_git.spec.ts`)
- **Tool**: Jest (`*.spec.ts`), run in band against a live CodeMie environment
- **Run command**: `npm run test:e2e` (from `sdk/codemie-nodejs`). Not part of CI.
- **Setup**: copy `sdk/codemie-nodejs/.env.e2e.example` to `.env.e2e` and fill in the values. `tests/e2e/setup.ts` loads that file and sets a 5-minute test timeout. Never commit `.env.e2e` (see `.ai-run/guides/safety-no-go.md`).
- **Example**: `sdk/codemie-nodejs/tests/e2e/specs/assistant.spec.ts:35` (`should fetch prebuilt assistants`)

Platform e2e suite:
- The platform-wide end-to-end, integration and UI suites live in the public test harness repository, https://github.com/codemie-ai/codemie-test-harness. It drives the platform through the Python SDK, so a change to a public SDK name or model can break the harness. Check it when you rename or remove an export.

## Coverage Targets

- **Line coverage target**: not configured
- **Branch coverage target**: not configured
- **Coverage command**: not configured in CI. To measure locally:
  - Python: `poetry run pytest tests/ --cov=codemie_sdk --cov-report=term` (`pytest-cov` is in the `dev` group of `pyproject.toml`)
  - Node.js: `npx jest --config jest.config.mjs --coverage`

Current numbers: `.ai-run/guides/testing/qa-health.md`.

## Conventions

- **Test file naming**: Python `test_<area>.py`; Node.js unit `<area>.test.ts`; Node.js e2e `<area>.spec.ts`.
- **Test file location**: in a separate `tests/` directory of each SDK, not next to the source.
- **Test style**: Python uses pytest functions with `assert`, in some files grouped in `Test*` classes, and `@pytest.mark.parametrize` for tables (`sdk/codemie-python/tests/test_export_model_fields.py`). Node.js uses `describe` / `it` (unit) and `describe` / `test` (e2e).
- **Mocking the HTTP layer**:
  - Python: patch the `requests` call inside the shared helper, for example `patch("codemie_sdk.utils.http.requests.get")` (`sdk/codemie-python/tests/test_marketplace_management_service.py:73`). Build fake responses with `MagicMock` (`sdk/codemie-python/tests/test_user_lifecycle_service.py:33`).
  - Node.js: mock the whole HTTP module with `jest.mock("../../../src/utils/http", ...)` (`sdk/codemie-nodejs/tests/unit/services/user.test.ts:7`).
- **Cross-SDK parity check**: `sdk/codemie-python/tests/test_integration_models.py:57` compares the Python `CredentialTypes` enum with the Node.js model. It skips itself when the Node.js sources are not present.
- **Source docs scanned**: `README.md`, `CONTRIBUTING.md`, `AGENTS.md`, `CLAUDE.md`, `.ai-run/guides/*.md`, `.ai-run/guides/standards/*.md`, `.claude/skills/codemie-release/SKILL.md`, `docs/RELEASING.md`.
- **Naming / selector conventions (from docs)**: none documented. The SDKs have no UI, so there are no `data-testid` selectors.
- **Architecture notes (from docs)**:
  - One service class per API area, with one model module per area (`.ai-run/guides/architecture.md`). Tests follow the same split: one test file per area.
  - The two SDKs mirror the same platform API by hand; they are not generated from each other.
- **Testing guidance (from docs)**:
  - Add or update tests with every behaviour change (`AGENTS.md`, rule 5).
  - Unit tests must run without a live platform. Test the SDK behaviour (request shape, response parsing, errors), not the platform (`.ai-run/guides/development.md`, section "Tests").
  - Use placeholder hosts such as `https://your-codemie-host.example.com` in tests (`CONTRIBUTING.md`).
  - Do not use `make verify` as a test gate; it does not run the tests (`.ai-run/guides/quality-gates.md`).

## Anti-Patterns (observed in this codebase)

| Bad | Better | Why |
|---|---|---|
| Replace a private attribute: `service._api = dummy_api` (`sdk/codemie-python/tests/test_assistant_versions.py:51`) | Patch the transport, `patch("codemie_sdk.utils.http.requests.get")` (`sdk/codemie-python/tests/test_marketplace_management_service.py:73`) | A test that swaps `_api` breaks when the service is refactored, and it does not check the real request that the HTTP helper sends. |
| `make verify` as the check before a push (`sdk/codemie-python/Makefile`) | `poetry run pytest tests/` and the other CI commands | `verify: ruff tests` names a target that does not exist, so make runs no tests. |
| `pythonpath = codemie-python` in `sdk/codemie-python/pytest.ini:3` | Rely on the package that `poetry install` installs | The path points to a directory that does not exist. Tests import `codemie_sdk` from the installed package. |
| A filter that hides `PytestUnknownMarkWarning` (`sdk/codemie-python/pytest.ini:5`) | Register custom marks in `pytest.ini` | A typo in a mark name then silently runs or skips the wrong tests. |

## Code Repositories

Application/feature source repositories that will be tested (not test-only repos). Recorded for
qa-e2e-generator to search merge requests/commits by ticket ID — not scanned for conventions.

- **CodeMie SDK (Python and Node.js)**: https://github.com/codemie-ai/codemie-sdk

## External Sources

### Test Case Management
- **System**: none. Bugs and test gaps are tracked as GitHub Issues in this repository.
- **Adapter**: not available

> **No test case management system is used.** Test cases live as code in the test directories above. No adapter is configured.

### QA Documentation
- **System**: within repo
- **Adapter**: not configured
- **Paths**: `.ai-run/guides/testing/qa-strategy.md`, `.ai-run/guides/testing/qa-health.md`, `.ai-run/guides/quality-gates.md`

### External Test Repositories
none. The platform test harness (https://github.com/codemie-ai/codemie-test-harness) is a consumer of this SDK, not a test repository for it.
