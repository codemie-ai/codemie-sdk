# Development

For every command (install, lint, format, test, build) see `quality-gates.md`. This file does not repeat them.

## Workflow

1. Create a branch from `main`. Naming: `git-workflow.md`.
2. Change one SDK, or both when the platform API area exists in both. See `architecture.md`.
3. Add or update tests in the same change. Python tests are in `sdk/codemie-python/tests/`, Node.js tests in `sdk/codemie-nodejs/tests/`.
4. Run the gates for each SDK you changed. All gates must pass before you open a PR.
5. Open a PR. Commit and PR rules: `git-workflow.md`.

## Adding an API area

- Python: a model module in `models/`, a service module in `services/`, and a service attribute on the client in `client/client.py`. Export public names from `__init__.py`.
- Node.js: a model in `models/`, a service in `services/`, wired into `client/client.ts` and exported from `index.ts`.
- Use placeholder hosts such as `https://your-codemie-host.example.com` in examples and tests.

## Tests

- Unit tests must run without a live platform.
- The Node.js end-to-end suite needs a running CodeMie environment. It is not part of CI.
- Test the behaviour of the SDK (request shape, response parsing, errors), not the platform.

## Dependencies

- Python dependencies are locked in `sdk/codemie-python/poetry.lock`. The Node.js package has no lock file.
- Pin versions as the existing manifests do (`pyproject.toml`, `package.json`).
