# Code quality

Linters and formatters decide style: ruff for Python (version range in `sdk/codemie-python/pyproject.toml`, locked in `sdk/codemie-python/poetry.lock`), Biome for Node.js (`sdk/codemie-nodejs/biome.json`). Do not argue with them in review. How to run them: `.ai-run/guides/quality-gates.md`.

## General rules

- Keep a change small and focused on one thing.
- Public names of an SDK are its contract. Do not rename or remove an export without saying so in the PR.
- Do not catch an error to hide it. Raise the SDK exception types (Python: `exceptions.py`).
- No credentials, private hostnames or ticket keys in code, tests or comments.
- A comment points to a guide by file name and section name, not to a line number.

## Pydantic models

Python models use two config styles, by purpose:

- API response models use `extra="ignore"` (see `models/assistant.py`, symbol `model_config`). The platform may add fields; the SDK must not break on them.
- Builder input models use `extra="forbid"` together with `frozen=True`. A typo in an argument must fail at construction, and a built definition must be safe to reuse. See `builders/workflow/definition.py`, symbol `_MIRRORED_MODEL_CONFIG`.

Do not use `extra="forbid"` on a response model. Do not use `extra="ignore"` on a builder input model.

## TypeScript

- Validate API data with the zod schemas in `schemas/`.
- Keep the Biome lint clean with zero warnings; the lint script treats warnings as errors.
