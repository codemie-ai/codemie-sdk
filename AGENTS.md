# AGENTS.md

Two client SDKs for the CodeMie platform: `sdk/codemie-python` and `sdk/codemie-nodejs`. Read the guides below before you change code. Each guide owns one topic.

## Guides

| Topic | Guide |
|-------|-------|
| Packages, ticket and PR tools | [project.md](.ai-run/guides/project.md) |
| Code layout of both SDKs | [architecture.md](.ai-run/guides/architecture.md) |
| Day-to-day workflow, adding an API area | [development.md](.ai-run/guides/development.md) |
| Style, Pydantic models, error handling | [code-quality.md](.ai-run/guides/code-quality.md) |
| All commands: lint, format, test, build | [quality-gates.md](.ai-run/guides/quality-gates.md) |
| Secrets, internal references, vulnerability reports | [security.md](.ai-run/guides/security.md) |
| Branches, commits, PRs, releases | [git-workflow.md](.ai-run/guides/git-workflow.md) |

## Critical rules

1. Run the gates in `quality-gates.md` for each SDK you changed before you open a PR. Do not trust `make verify`; the guide says why.
2. Use Conventional Commits. No ticket key in branch, commit, PR title or PR body.
3. No credentials, private hostnames, personal paths or real ticket keys in any file. Use placeholders.
4. Do not publish a package by hand. Releases follow `docs/RELEASING.md`.
5. Add or update tests with every behaviour change.
6. Edit the guides in this repository. Keep one topic in one guide, and keep commands only in `quality-gates.md`.
