# Quality Gates

Run order is fastest-to-slowest.

## Full runs

| Command | Covers | Source |
|---|---|---|
| `cd sdk/codemie-python && poetry install --no-interaction && poetry run ruff check . && poetry run ruff format --check . && poetry run pytest tests/ && poetry build` | install, lint, format check, unit tests, build (what CI job python runs on a PR) | .github/workflows/ci.yml::jobs.python |
| `cd sdk/codemie-nodejs && npm install --no-audit --no-fund && npm run lint && npm test && npm run build` | install (prepare also builds), lint of src/, unit tests, build (what CI job node runs on a PR) | .github/workflows/ci.yml::jobs.node |
| `scripts/release/dry_run.sh python python-vX.Y.Z` | registry version check (network), stamped copy, lint, unit tests, build; no format check; publishes nothing | scripts/release/dry_run.sh |
| `scripts/release/dry_run.sh node node-vX.Y.Z` | registry version check (network), stamped copy, lint, unit tests, build, npm pack; publishes nothing | scripts/release/dry_run.sh |
| `CI on a PR: ci.yml (python, node, internal-refs, secrets-detection), pr-title-lint.yml (PR title), codeql.yml (CodeQL)` | both SDK jobs, internal-reference and secret scans, PR-title commitlint, CodeQL | .github/workflows/ci.yml |

---

### lint-python

**Run**: `cd sdk/codemie-python && poetry run ruff check .`
**Pass**: exit 0, no violations reported
**Fail**: non-zero exit with one line per violation
**Auto-fix**: cd sdk/codemie-python && make ruff-fix

### format-python

**Run**: `cd sdk/codemie-python && poetry run ruff format --check .`
**Pass**: exit 0, every file already formatted
**Fail**: non-zero exit listing files that would be reformatted
**Auto-fix**: cd sdk/codemie-python && make ruff-format
**Notes**: publish-python.yml and scripts/release/dry_run.sh do not run the format check

### test-python

**Run**: `cd sdk/codemie-python && make test`
**Pass**: pytest exit 0
**Fail**: pytest non-zero exit with failing test ids

### lint-nodejs

**Run**: `cd sdk/codemie-nodejs && npm run lint`
**Pass**: exit 0, no diagnostics
**Fail**: non-zero exit on any error or warning in src/

### test-nodejs

**Run**: `cd sdk/codemie-nodejs && npm test`
**Pass**: jest exit 0
**Fail**: jest non-zero exit with failing suites

## Python SDK (`sdk/codemie-python`)

Run the gates from `sdk/codemie-python`. CI uses Python 3.13 (`actions/setup-python`) and installs Poetry with `pipx install poetry`; the release workflow `publish-python.yml` uses Python 3.12.

Warning about `make verify`: the target is defined as `verify: ruff tests`. The Makefile has no `tests` target (the real target is `test`). Because the directory `tests/` exists, make treats `tests` as an up-to-date file and runs nothing for it. So `make verify` runs only `make ruff` and never runs the tests. It also rewrites files (`--fix`, `ruff format`), while CI only checks. Run the gates above instead.

Releases go through `docs/RELEASING.md`, never `make publish`.

## Node.js SDK (`sdk/codemie-nodejs`)

Run the gates from `sdk/codemie-nodejs`. CI uses Node 20. The package has no committed lock file, so CI installs with `npm install --no-audit --no-fund`; `npm ci` does not work.

`npm run format` writes files and `npm run test:e2e` needs a live platform; neither is a gate or part of CI.

`npm install` runs the `prepare` script, which builds `dist/`. `npm pack` runs `prepack` (unit tests, then lint). CI has no Biome format check.

## Repository checks

The CI jobs `internal-refs` ("Internal references") and `secrets-detection` ("Security") use reusable workflows. They scan for internal e-mail addresses, internal hosts, ticket keys and secrets; no rule covers personal paths. `.github/workflows/codeql.yml` runs CodeQL for actions, JavaScript/TypeScript and Python on PRs to `main`, pushes to `main` and weekly. See `.ai-run/guides/security.md`.
