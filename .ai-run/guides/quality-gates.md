# Quality gates

This file is the only place that holds commands. Other guides link here.
Source of truth: `.github/workflows/ci.yml` (jobs `python`, `node`), `sdk/codemie-python/Makefile`, `sdk/codemie-nodejs/package.json` (section `scripts`).

## Python SDK (`sdk/codemie-python`)

Run all commands from `sdk/codemie-python`. CI uses Python 3.12 (`actions/setup-python`) and installs Poetry with `pipx install poetry`.

CI job "Python SDK" (`.github/workflows/ci.yml`, job `python`) then runs these steps in order:

1. `poetry install --no-interaction`
2. `poetry run ruff check .`
3. `poetry run ruff format --check .`
4. `poetry run pytest tests/`
5. `poetry build`

Makefile targets (`sdk/codemie-python/Makefile`):

| Target | What it runs |
|--------|--------------|
| `make install` | `poetry install` |
| `make test` | `poetry run pytest tests/` |
| `make ruff` | `poetry run ruff check --fix`, then `poetry run ruff check`, then `poetry run ruff format` |
| `make ruff-format` | `poetry run ruff format` |
| `make ruff-fix` | `poetry run ruff check --fix` |
| `make verify` | see the warning below |
| `make build` | `poetry build` |

Warning about `make verify`: the target is defined as `verify: ruff tests`. The Makefile has no `tests` target (the real target is `test`). Because the directory `tests/` exists, make treats `tests` as an up-to-date file and runs nothing for it. So `make verify` runs only `make ruff` and never runs the tests. It also rewrites files (`--fix`, `ruff format`), while CI only checks.

Before you push, run the CI commands, not `make verify`:

```
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest tests/
poetry build
```

Anti-pattern: do not run `make publish` (`poetry publish`). Releases go through the process in `docs/RELEASING.md`.

## Node.js SDK (`sdk/codemie-nodejs`)

Run all commands from `sdk/codemie-nodejs`. CI uses Node 20.

CI job "Node.js SDK" (`.github/workflows/ci.yml`, job `node`) runs these steps in order:

1. `npm install --no-audit --no-fund` (the package has no committed lock file, so `npm ci` does not work)
2. `npm run lint`
3. `npm test`
4. `npm run build`

Other scripts in `package.json`: `npm run format` (writes files), `npm run test:e2e` (needs a live platform; not part of CI).

## Repository checks

The CI jobs `internal-refs` ("Internal references") and `secrets-detection` ("Security") use reusable workflows. They scan for internal ticket keys, internal hosts, personal paths and secrets. See `.ai-run/guides/security.md`.
