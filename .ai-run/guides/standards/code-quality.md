# Code quality

Linters and formatters decide style: ruff for Python (version range in `sdk/codemie-python/pyproject.toml`, locked in `sdk/codemie-python/poetry.lock`), Biome for Node.js (`sdk/codemie-nodejs/biome.json`). Do not argue with them in review. How to run them: `.ai-run/guides/quality-gates.md`.

## General rules

- Keep a change small and focused on one thing.
- Public names of an SDK are its contract. Do not rename or remove an export without saying so in the PR.
- Do not catch an error to hide it. Raise the SDK exception types (Python: `exceptions.py`).
  - Known debt, to fix: no Python code raises or exports these types yet. `sdk/codemie-python/src/codemie_sdk/utils/http.py` (every verb calls `raise_for_status()`), `exceptions.py`, `__init__.py`, `services/dynamic_config.py` and `services/assistant.py` (catch `HTTPError` by status), `auth/credentials.py` (`_decode_jwt_exp` swallows every exception).
- No credentials, private hostnames or ticket keys in code, tests or comments.
- A comment points to a guide by file name and section name, not to a line number.

## Pydantic models

Python models use these config styles, by purpose:

- API response models use `extra="ignore"` (see `models/assistant.py`, symbol `model_config`). The platform may add fields; the SDK must not break on them.
- Builder input models use `extra="forbid"` together with `frozen=True`. A typo in an argument must fail at construction, and a built definition must be safe to reuse. See `builders/workflow/definition.py`, symbol `_MIRRORED_MODEL_CONFIG`.
- Typed datasource request models use `extra="forbid"` without `frozen=True`, so an unknown key fails at construction (see `models/datasource.py`, symbol `SvnDataSourceRequest`).
- A few response models use `extra="allow"` to keep fields the SDK does not declare (see `models/workflow.py`, symbol `WorkflowGeneratorConfig`).

Do not use `extra="forbid"` on a response model. Do not use `extra="ignore"` on a builder input model.

## TypeScript

- Parse caller parameters with the matching `*ParamsSchema` from `schemas/` before the request, as `services/workflow.ts` does in `create` and `list`. The `category`, `datasource`, `files`, `llm`, `task` and `user` services take typed parameters without a schema.
- Keep the Biome lint clean with zero warnings; the lint script treats warnings as errors and lints `src/` only, so `tests/` is not linted.
- Let HTTP errors reach the caller: the response interceptor in `utils/http.ts` (`processFailedResponse`) turns a status of 400 or more into `ApiError`, and every 404 into `NotFoundError("Resource", "unknown")`.
