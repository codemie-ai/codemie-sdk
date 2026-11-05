# Project

This repository holds two client SDKs for the CodeMie platform.

| Package | Path | Registry name | Language |
|---------|------|---------------|----------|
| Python SDK | `sdk/codemie-python` | `codemie-sdk-python` | Python 3.12, Poetry |
| Node.js SDK | `sdk/codemie-nodejs` | `codemie-sdk` | TypeScript, npm |

Each package is built, tested and released on its own. Commands: `quality-gates.md`. Layout: `architecture.md`.

## Ticket Adapter

- Tracker: Jira.
- Tool: the `codemie-jira-assistant` CodeMie assistant.
- Ticket keys look like `EPMCDME-NNNNN`. Use only this placeholder form in files, commits, branches and PRs of this repository. Never write a real key.
- External contributors do not need Jira. They use GitHub Issues, and a PR closes its issue with `Closes #N`.

## MR Adapter

- Host: GitHub, organisation `codemie-ai`.
- Create a pull request with `gh pr create`.
- The PR title follows Conventional Commits. See `git-workflow.md`.
- The PR template is `.github/PULL_REQUEST_TEMPLATE.md`.

## Related repositories

The platform backend, the UI, the test harness and the infrastructure code are separate repositories. A change to a platform catalog (tool names, integration types, credential types) may also need a change in the backend. This repository follows the backend; it does not drive it.
