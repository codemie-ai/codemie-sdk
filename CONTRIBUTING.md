# Contributing

Contributions are welcome. Please read the [Code of Conduct](CODE_OF_CONDUCT.md) before you start.

This repository contains two SDKs: `sdk/codemie-python` and `sdk/codemie-nodejs`.

## How to Contribute

1. Fork the repository on GitHub.
2. Clone your fork and create a branch: `git checkout -b my-feature-branch`.
3. Make your change and add or update tests.
4. Run the checks for the SDK you changed (see below).
5. Push the branch to your fork and open a pull request against `main`.

## Pull Requests

- The PR title must follow [Conventional Commits](https://www.conventionalcommits.org/): `<type>(<optional scope>): <description>`, for example `feat(python): add assistant versioning helper` or `fix(nodejs): handle empty response`.
- Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- Keep a PR focused on one change. Describe what changed and why.
- Individual commit messages are not checked.

## SDK Parity

The two SDKs must stay in step: a service or method added or changed in one SDK needs the matching change in the other, or a recorded gap. See the [parity guide](docs/PARITY.md) for naming and known differences.

## Review Rule

Every PR needs one approval from any collaborator with write access before it can be merged. All CI checks must pass.

## Python SDK (`sdk/codemie-python`)

```bash
cd sdk/codemie-python
poetry install
poetry run ruff check .
poetry run pytest tests/
poetry build
```

## Node.js SDK (`sdk/codemie-nodejs`)

```bash
cd sdk/codemie-nodejs
npm install
npm run lint
npm test
npm run build
```

The end-to-end suite (`npm run test:e2e`) needs a running CodeMie environment. It does not run in CI.

## Internal References and Secrets

CI scans the tree for internal references and for secrets. Do not commit credentials, private hostnames, ticket keys, or personal e-mail addresses. Use placeholders such as `https://your-codemie-host.example.com` in examples and tests.

## Reporting Issues

Use GitHub Issues for bugs and feature requests. For security problems, follow [SECURITY.md](SECURITY.md).
