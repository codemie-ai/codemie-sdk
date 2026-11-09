# Safety no-go list

Rules for every AI agent and every person who works in this repository. Do not do these things, even when a task seems to need them. If a task cannot be done without one of them, stop and ask a maintainer.

Claude Code enforces the same list through `.claude/settings.json` (`permissions.deny`, and `permissions.ask` for releases). Other agents (Codex, Gemini, Copilot and others) do not read that file, so they must follow this guide. When you change one file, change the other in the same PR.

Related guides: `.ai-run/guides/security.md` (secrets and CI scans), `.ai-run/guides/standards/git-workflow.md` (branches, releases).

## Files never read or changed

| Path | Why |
|------|-----|
| `.env`, `.env.local`, `.env.*.local`, `.env.e2e`, `.env.development`, `.env.test`, `.env.production` | They hold real platform credentials (for example the Node.js e2e suite loads `sdk/codemie-nodejs/.env.e2e`). Reading them puts secrets in the agent context and logs. |
| `*.pem`, `*.key`, `*.p12`, `*.pfx` | Private keys and certificates. A leaked key cannot be taken back. |
| `~/.ssh/**`, `~/.aws/**` | Personal SSH keys and cloud credentials. They are outside the repository and outside the task. |
| `~/.npmrc`, `~/.pypirc` | Registry tokens that can publish packages. |
| `sdk/codemie-python/poetry.lock` (no hand edits) | Poetry generates it. A hand edit breaks the content hash, and `poetry install` in CI then fails. Change `pyproject.toml` and run Poetry. |
| `package-lock.json` (no hand edits, no commit) | The Node.js SDK has no committed lock file on purpose; CI runs `npm install` (see `.ai-run/guides/quality-gates.md`). |

You may read the committed template `sdk/codemie-nodejs/.env.e2e.example`. It holds only placeholders. Put real values only in your local `.env.e2e`, which git ignores.

## Commands never run

| Command | Why |
|---------|-----|
| `git push --force`, `git push -f`, `git push <remote> --force-with-lease` | It rewrites shared history and can delete the work of other people. Push a new commit instead. |
| `git reset --hard` | It deletes uncommitted work with no undo. Use `git stash` or a new branch. |
| `git clean -f`, `git clean -fd`, `git clean -xfd` | It deletes untracked files, which can be local notes, `.env` files or work in progress. |
| `rm -rf <path>` | A wrong path deletes files with no undo. Delete named files one by one. |
| `git commit --no-verify`, any command with `--no-verify` | It skips hooks and checks. Fix the failing check instead. |
| `poetry publish`, `make publish`, `npm publish`, `npm dist-tag`, `twine upload` | Releases go only through the GitHub Release workflow in `docs/RELEASING.md`. A hand upload skips the version gate and the checks. |
| `git push --tags`, `git push <remote> python-v*`, `git push <remote> node-v*`, `git push <remote> refs/tags/*` | A tag names a release version. A wrong tag on the remote can block or confuse a release. |
| `gh workflow run publish-python.yml`, `gh workflow run publish-node.yml` | A manual dispatch can publish a package to a public registry. |

## Actions that always need a person

| Action | Why |
|--------|-----|
| `gh release create`, `gh release edit`, `gh release delete` | A published GitHub Release starts the publish workflow, and a version on PyPI or npm cannot be changed or removed. The `codemie-release` skill runs this step only after an explicit "yes" from the user; Claude Code also asks before it runs. |
| Approval of the `release` environment in GitHub Actions | It is the last gate before the upload to a public registry. |
| Merge of a PR to `main` | Every PR needs one approval from a collaborator with write access (`CONTRIBUTING.md`, section "Review Rule"). |
| A change to `.github/workflows/`, `.gitleaks.toml` or `.claude/settings.json` | These files control CI, secret scans and agent permissions. A maintainer must review the change on purpose. |
