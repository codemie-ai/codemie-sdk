# QA Health

**Last assessed**: 2026-11-12
**Coverage**: Python SDK 86% lines; Node.js SDK 76.9% lines, 62.6% branches

Measured once, locally, on 2026-11-12, with the unit suites only (the Node.js e2e suite needs a live platform and was not run). CI does not collect coverage, so these numbers are a snapshot. To measure again, use the coverage commands in `.ai-run/guides/testing/qa-strategy.md`, section "Coverage Targets".

| SDK | Tests | Result | Lines | Branches |
|---|---|---|---|---|
| Python (`poetry run pytest tests/ --cov=codemie_sdk`) | 514 | all passed | 86% (4425 of 5174 statements) | not measured |
| Node.js (`npx jest --config jest.config.mjs --coverage`) | 329 in 26 suites | all passed | 76.9% (632 of 822) | 62.6% (258 of 412) |

## Coverage Summary

| Module / area | Coverage | Notes |
|---|---|---|
| Python `models/` | 92-100% per module (`models/errors.py` 74%) | Models are covered through the service and model tests. |
| Python `builders/workflow/` | 97-100% | The best covered area. Six test files (`test_workflow_*.py`), including the README examples. |
| Python `client/client.py` | 94% | |
| Python `auth/credentials.py` | 81% | |
| Python `utils/http.py` | 83% | |
| Python `services/` | 26-100% per module, most between 40% and 60% | Many services are covered only by import and model tests, not by request tests. |
| Python `exceptions.py` | 60% | |
| Node.js `mappers/`, `models/`, `schemas/`, `exceptions/` | 91-100% (`models/errors.ts` 65%) | |
| Node.js `auth/credentials.ts` | 100% lines, 85% branches | |
| Node.js `client/client.ts` | 76% lines, 58% branches | |
| Node.js `utils/http.ts` | 84% lines, 78% branches | `tests/unit/utils/` tests it directly. The service tests mock it. |
| Node.js `services/` | 8-100% per module | `user`, `task`, `llm`, `files`, `integration`, `workflow*` at 100% lines. |

## Risky Untested Areas

Modules with zero or low coverage that carry business logic:

| Path | Coverage | Risk reason |
|---|---|---|
| `sdk/codemie-python/src/codemie_sdk/services/vendor_assistant.py`, `vendor_guardrail.py`, `vendor_knowledgebase.py`, `vendor_runtime.py`, `vendor_workflow.py` | 35-43% | No test file names them. Cloud vendor install and uninstall flows have no request-shape tests. |
| `sdk/codemie-python/src/codemie_sdk/services/activity_event.py` | 26% | No test file. |
| `sdk/codemie-python/src/codemie_sdk/services/dynamic_config.py` | 26% | No test file. Admin configuration writes. |
| `sdk/codemie-python/src/codemie_sdk/services/project_budget_groups.py` | 29% | No test file. Budget data. |
| `sdk/codemie-python/src/codemie_sdk/services/admin.py` | 40% | Admin operations. Only the admin models have tests (`test_admin_user_models.py`). |
| `sdk/codemie-python/src/codemie_sdk/services/conversation.py`, `skill.py`, `integration.py` | 42-47% | Core user-facing areas with low request coverage. |
| `sdk/codemie-nodejs/src/services/analytics.ts` | 8% lines, 0% branches | No unit test file. |
| `sdk/codemie-nodejs/src/services/category.ts` | 33% lines, 0% branches | No unit test file. |
| `sdk/codemie-nodejs/src/services/skill.ts` | 33% lines, 0% branches | `tests/unit/services/skill.test.ts` covers the limits, companion files and visibility, but leaves most methods out. |
| `sdk/codemie-nodejs/src/services/conversation.ts` | 36% lines, 0% branches | |

## Known Test Debt

No QA documents or test plans are in the repository. Gaps found in the code:

- No coverage gate. CI runs the unit tests but does not measure or limit coverage.
- The Node.js e2e suite (`sdk/codemie-nodejs/tests/e2e/`) does not run in CI and needs a live platform, so it can fall behind the code.
- The Python `test` dependency group in `sdk/codemie-python/pyproject.toml` lists packages that no test in this repository imports (`boto3`, `python-gitlab`, `pytest-playwright`, `PyHamcrest`, `codemie-plugins`, `aws-assume-role-lib`, `python-dotenv`, `pytest-xdist`, `pytest-rerunfailures`, `tzlocal`). They make `poetry install` slow.
- `sdk/codemie-python/pytest.ini` sets `pythonpath` to a directory that does not exist and hides unknown-mark warnings (see `qa-strategy.md`, section "Anti-Patterns").
- The Python and Node.js SDKs do not have the same test depth for the same area (for example skills: Python `test_skill_models.py` covers the models and the `visibility` field on create, update and import; Node.js `skill.test.ts` covers a few methods).

## Recent Test Activity

From `git log --diff-filter=AM -n 5 --name-only --pretty='' -- 'sdk/*test*' 'sdk/*spec*'` on 2026-11-12:

- `sdk/codemie-python/tests/test_user_lifecycle_service.py`
- `sdk/codemie-python/tests/test_workflow_builder.py`
- `sdk/codemie-python/tests/test_workflow_definition.py`
- `sdk/codemie-python/tests/test_assistant_integration_serialization.py`
- `sdk/codemie-python/tests/test_integration_serialization.py`
