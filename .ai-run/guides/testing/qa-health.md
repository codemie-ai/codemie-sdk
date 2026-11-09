# QA Health

**Last assessed**: 2026-11-09
**Coverage**: Python SDK 85% lines; Node.js SDK 74.9% lines, 58% branches

Measured once, locally, on `main` with the unit suites only (the Node.js e2e suite needs a live platform and was not run). CI does not collect coverage, so these numbers are a snapshot. To measure again, use the coverage commands in `.ai-run/guides/testing/qa-strategy.md`, section "Coverage Targets".

| SDK | Tests | Result | Lines | Branches |
|---|---|---|---|---|
| Python (`poetry run pytest tests/ --cov=codemie_sdk`) | 443 | all passed | 85% (4294 of 5060 statements) | not measured |
| Node.js (`npx jest --config jest.config.mjs --coverage`) | 302 in 24 suites | all passed | 74.9% (603 of 805) | 58% (222 of 383) |

## Coverage Summary

| Module / area | Coverage | Notes |
|---|---|---|
| Python `models/` | 92-100% per module (`models/errors.py` 74%) | Models are covered through the service and model tests. |
| Python `builders/workflow/` | 97-99% | The best covered area. Five test files (`test_workflow_*.py`), including the README examples. |
| Python `client/client.py` | 94% | |
| Python `auth/credentials.py` | 81% | |
| Python `utils/http.py` | 83% | |
| Python `services/` | 26-100% per module, most between 40% and 60% | Many services are covered only by import and model tests, not by request tests. |
| Python `exceptions.py` | 60% | |
| Node.js `mappers/`, `models/`, `schemas/`, `exceptions/` | 91-100% (`models/errors.ts` 65%) | |
| Node.js `auth/credentials.ts` | 100% lines, 85% branches | |
| Node.js `client/client.ts` | 76% lines, 58% branches | |
| Node.js `utils/http.ts` | 56% lines, 40% branches | The unit tests mock this module for every service test. |
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
| `sdk/codemie-python/src/codemie_sdk/services/conversation.py`, `skill.py`, `integration.py` | 42-44% | Core user-facing areas with low request coverage. |
| `sdk/codemie-nodejs/src/services/analytics.ts` | 8% lines, 0% branches | No unit test file. |
| `sdk/codemie-nodejs/src/services/category.ts` | 33% lines, 0% branches | No unit test file. |
| `sdk/codemie-nodejs/src/services/skill.ts` | 30% lines, 0% branches | `tests/unit/services/skill.test.ts` has 7 tests but leaves most methods out. |
| `sdk/codemie-nodejs/src/services/conversation.ts` | 36% lines, 0% branches | |
| `sdk/codemie-nodejs/src/utils/http.ts` | 56% lines, 40% branches | Shared by every service. The error mapping paths (`NotFoundError`, `ApiError`) are only partly covered. |

## Known Test Debt

No QA documents or test plans are in the repository. Gaps found in the code:

- No coverage gate. CI runs the unit tests but does not measure or limit coverage.
- The Node.js e2e suite (`sdk/codemie-nodejs/tests/e2e/`) does not run in CI and needs a live platform, so it can fall behind the code.
- The Python `test` dependency group in `sdk/codemie-python/pyproject.toml` lists packages that no test in this repository imports (`boto3`, `python-gitlab`, `pytest-playwright`, `PyHamcrest`, `codemie-plugins`, `aws-assume-role-lib`, `python-dotenv`, `pytest-xdist`, `pytest-rerunfailures`, `tzlocal`). They make `poetry install` slow.
- `sdk/codemie-python/pytest.ini` sets `pythonpath` to a directory that does not exist and hides unknown-mark warnings (see `qa-strategy.md`, section "Anti-Patterns").
- The Python and Node.js SDKs do not have the same test depth for the same area (for example skills: Python `test_skill_models.py` covers models only; Node.js `skill.test.ts` covers a few methods).

## Recent Test Activity

From `git log --diff-filter=AM -n 5 --name-only --pretty='' -- '*test*' '*spec*'` on 2026-11-09:

- `sdk/codemie-python/tests/test_assistant_share.py`
- `sdk/codemie-python/tests/test_marketplace_management_service.py`
- `sdk/codemie-python/tests/test_export_service.py`
- `sdk/codemie-python/tests/test_prompt_variables.py`
- `sdk/codemie-python/tests/test_user_lifecycle_service.py`
