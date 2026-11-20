# Development

For every command (install, lint, format, test, build) see `.ai-run/guides/quality-gates.md`. This file does not repeat them.

## Workflow

1. Create a branch from `main`. Naming: `.ai-run/guides/standards/git-workflow.md`.
2. Change one SDK, or both when the platform API area exists in both. See `.ai-run/guides/architecture.md`.
3. Add or update tests in the same change. Python tests are in `sdk/codemie-python/tests/`; Node.js unit tests are in `sdk/codemie-nodejs/tests/unit/` as `*.test.ts`, the only root `jest.config.mjs` reads.
4. Run the gates for each SDK you changed. All gates must pass before you open a PR.
5. Open a PR. Commit and PR rules: `.ai-run/guides/standards/git-workflow.md`.

## Adding an API area

- Python: a model module in `models/`, a service module in `services/`, and a service attribute on the client in `client/client.py`. Export public names from `__init__.py`.
- Python: a service takes `(api_domain, token, verify_ssl=True)` and builds its own `ApiRequestHandler`. Pass `token` through unchanged: the client hands over `get_token` as a callable, and `ApiRequestHandler._get_headers` calls it on every request, so a token resolved to a string in the service stops refreshing.
- Python: pass `wrap_response=False` when a response carries `data` next to other top-level fields; by default `ApiRequestHandler._parse_response` keeps only the `data` value (see `services/usage_attribution.py`).
- Node.js: a model in `models/`, a service in `services/` (and a `*ParamsSchema` in `schemas/` when it takes parameters), wired into `client/client.ts` (a private field, a getter and a `new XService(authConfig)` line) and re-exported from `src/models/index.ts`, `src/services/index.ts` and `src/schemas/index.ts`; `src/index.ts` only re-exports those barrels.
- Use placeholder hosts such as `https://your-codemie-host.example.com` in examples and tests.

## Tests

- Unit tests must run without a live platform.
- The Node.js end-to-end suite needs a running CodeMie environment. It is not part of CI.
- Test the behaviour of the SDK (request shape, response parsing, errors), not the platform.
- Python unit tests patch `codemie_sdk.utils.http.requests.<verb>` and assert on `call_args` (see `tests/test_usage_attribution_service.py`). Node.js unit tests replace `ApiRequestHandler` with `jest.mock("../../../src/utils/http")` (see `tests/unit/services/workflow.test.ts`).

## Dependencies

- Python dependencies are locked in `sdk/codemie-python/poetry.lock`. The Node.js package has no lock file.
- Follow each manifest's version style: caret ranges in `pyproject.toml`, exact versions in `package.json`.
