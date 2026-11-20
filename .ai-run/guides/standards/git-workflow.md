# Git Workflow

**Project**: CodeMie SDK · **Stack**: Python (`sdk/codemie-python`), TypeScript (`sdk/codemie-nodejs`) · **Scope**: branch names, commit subjects, merge policy and their recovery steps; exact gate commands live in `.ai-run/guides/quality-gates.md`, the MR adapter in `.ai-run/guides/project.md`

## Branch Naming Convention

- base branch: github/main
- pattern: `<type>/<short-description>`

### Rules
- R1. Cut every branch from `github/main`, never from local `main` or `origin/main` (local `main` tracks the internal `origin` mirror, which shares no history with the public repository, so diffs and PRs against it are wrong). Evidence: `git merge-base main github/main` prints nothing; recorded user decision
- R2. Name the branch `<type>/<short-description>` in kebab case, for example `feat/assistant-versioning` or `docs/sdk-agent-guides` (the type matches the Conventional Commits type of the PR title). Evidence: `git branch -r` on the `fork` remote (`feat/*`, `fix/*`, `docs/*`, `ci/*`); recorded user decision
- R3. Use a type from `CONTRIBUTING.md`: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`. Evidence: `CONTRIBUTING.md` (Pull Requests)
- R4. Keep the ticket key out of the branch name (the public repository carries no internal ticket keys; a pushed branch name is public). Evidence: `CONTRIBUTING.md`

## Commit Message Format

```
<type>(<scope>)!?: <description>
```

Examples: `fix(python): reactivate users through the dedicated endpoint (#57)` · `ci(workflows): reuse npm and pypi publish workflows (#42)` · `feat(python)!: support A2A protocol v1.0 agent card (#36)`

### Rules
- R1. Write the PR title as a Conventional Commit `<type>(<optional scope>): <description>`. Scopes in the history of `github/main`: `python` and `workflows`; `CONTRIBUTING.md` uses `nodejs` for the Node.js SDK. Evidence: `CONTRIBUTING.md` (Pull Requests); `git log github/main`
- R2. Mark a breaking change with `!` before the colon, as in `feat(python)!: support A2A protocol v1.0 agent card (#36)` (the confirmed format is `<type>(<scope>)!?: <description>`). Evidence: `git log github/main`
- R3. Write individual commits in the same format: CI (`.github/workflows/pr-title-lint.yml`) checks only the title of a PR to `main`, with commitlint's conventional config, and reruns when the title is edited; individual commit messages are not checked. Evidence: `.github/workflows/pr-title-lint.yml`; `CONTRIBUTING.md`
- R4. Keep ticket keys out of commit messages, PR titles and PR bodies; an external contributor links a GitHub issue with `Closes #N`. Evidence: `CONTRIBUTING.md`

## Merge Strategy

### Rules
- R1. Squash-merge every PR into `main` on the `github` remote: the PR title becomes the commit subject on `main` and GitHub appends the PR number, as in `fix(python): reactivate users through the dedicated endpoint (#57)`, so the title must be a valid Conventional Commit. Evidence: recorded user decision; every subject on `github/main` since #4 ends with `(#N)`
- R2. Merge only with one approval from a collaborator with write access and every CI check green (`CONTRIBUTING.md` states the rule; the branch protection settings were not readable). Evidence: `CONTRIBUTING.md` (Review Rule)
- R3. Keep one focused change per PR and fill in `.github/PULL_REQUEST_TEMPLATE.md` (reviews and the squash subject stay scoped to one change). Evidence: `CONTRIBUTING.md` (Pull Requests); `.github/PULL_REQUEST_TEMPLATE.md`
- R4. Treat a merge to `main` as no release: a package is released only by a published GitHub Release whose tag names it (`python-vX.Y.Z[-rcN]` or `node-vX.Y.Z[-rcN]`); follow `docs/RELEASING.md` for the steps. Evidence: `docs/RELEASING.md`; `.github/workflows/publish-python.yml`; `.github/workflows/publish-node.yml`

## Anti-Patterns

| Do not | Do instead | Why |
|---|---|---|
| Name a branch `EPMCDME-NNNNN_assistant-versioning` | `feat/assistant-versioning` | ticket keys stay out of the public repository |
| Title a PR `EPMCDME-NNNNN: add versioning` | `feat(python): add assistant versioning helper` | the PR-title check fails and the squash subject on `main` would carry the key |
| Put a ticket link in the PR body | `Closes #N` for a GitHub issue; maintainers post the PR URL on the ticket (see `.ai-run/guides/project.md`) | ticket keys stay out of the public repository |
| Mix Python and Node.js changes for unrelated features in one PR | one focused PR per change | one squash commit per change keeps revert and review scoped |
| Publish from a laptop (`make publish`, `poetry publish`, `npm publish`) | publish a GitHub Release as `docs/RELEASING.md` describes | the tag is the version and the `verify` job gates the upload; the Node.js README publish section and the Python `make publish` target are stale |
| Edit a copy of the guides outside this repository or open an internal-sync PR | edit `.ai-run/guides` in this repository | the internal sync is stopped; no other copy is the source of truth |
| Cut a branch from local `main` or `origin/main` | `git fetch github && git switch -c <type>/<short-description> github/main` | local `main` tracks the internal mirror with unrelated history |

## Troubleshooting

| Issue | Fix |
|---|---|
| A diff or PR shows hundreds of unrelated commits | the branch was cut from local `main`: `git rebase --onto github/main main <branch>`, then `git push --force-with-lease` to your fork |
| The PR Title check fails | edit the PR title to `<type>(<optional scope>): <description>` with no ticket key; the check reruns on `edited`, no new commit needed |
| A commit message on the branch has the wrong format | nothing to rewrite before merge: the squash subject comes from the PR title; fix the title |
