# Git workflow

Sources: `CONTRIBUTING.md`, `docs/RELEASING.md`, `.github/workflows/pr-title-lint.yml`.

## Branches

- Branch from `main`.
- Name: `<type>/<short-description>`, for example `feat/assistant-versioning` or `docs/sdk-agent-guides`.
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- No ticket key in the branch name.

## Commits and PR title

- Use Conventional Commits: `<type>(<optional scope>): <description>`. Scopes in use: `python`, `nodejs`, `workflows`.
- The PR title is checked by CI. Individual commit messages are not, but follow the same format.
- No ticket key in a commit message, PR title or PR body. External contributors link their GitHub issue with `Closes #N`.
- One focused change per PR. Fill in `.github/PULL_REQUEST_TEMPLATE.md`.
- A PR needs one approval from a collaborator with write access and green CI.

## Merge strategy

Squash merge. The PR title becomes the commit subject on `main`, and GitHub adds the PR number, for example `fix(python): reactivate users through the dedicated endpoint (#57)`. So the PR title must be a valid Conventional Commit.

## Anti-patterns

| Avoid | Prefer |
|---|---|
| `EPMCDME-NNNNN_assistant-versioning` as a branch name | `feat/assistant-versioning` |
| `EPMCDME-NNNNN: add versioning` as a PR title | `feat(python): add assistant versioning helper` |
| A ticket link in the PR body | `Closes #N` for a GitHub issue; maintainers post the PR URL on the ticket (see `.ai-run/guides/project.md`) |
| Python and Node.js changes for unrelated features in one PR | One focused PR per change |

## Releases

Follow `docs/RELEASING.md`. This guide does not restate the steps. In short: a release is a GitHub Release with a tag per package (`python-v...` or `node-v...`). A merge to `main` does not release.

Anti-pattern: do not publish from a laptop (`make publish`, `poetry publish`, `npm publish`).

## Internal sync

The internal sync is stopped. The guides in `.ai-run/guides` are edited in this repository, and no other copy is the source of truth.
