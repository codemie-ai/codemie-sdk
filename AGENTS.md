# AGENTS.md

Two client SDKs for the CodeMie platform: `sdk/codemie-python` and `sdk/codemie-nodejs`. Read the guides listed under Guide Imports before you change code. Each guide owns one topic.

## Guide Imports

<!-- ai-run-init:guide-imports start -->
| Category | Guide Path | Purpose |
|---|---|---|
| Project | .ai-run/guides/project.md | Project identity, tracker and source control |
| Quality | .ai-run/guides/quality-gates.md | Quality gates and how to run them |
| Architecture | .ai-run/guides/architecture.md | Code layout of both SDKs and where each concern lives |
| Code Quality | .ai-run/guides/standards/code-quality.md | Style, Pydantic model configs, error handling, TypeScript rules |
| Development | .ai-run/guides/development.md | Day-to-day workflow, adding an API area, test conventions |
| Git Workflow | .ai-run/guides/standards/git-workflow.md | Branch naming, Conventional Commits PR titles, squash merge, releases |
| Security | .ai-run/guides/security.md | Secrets, internal references, TLS, logging, vulnerability reports |
<!-- ai-run-init:guide-imports end -->

## Task Classifier

<!-- ai-run-init:task-classifier start -->
| Category | User Intent | Example Requests | P0 Guide | P1 Guide |
|---|---|---|---|---|
| Architecture | find where code lives, understand SDK structure or parity | "where is the HTTP helper", "which SDK has the workflow builder" | .ai-run/guides/architecture.md | - |
| Code Quality | write or review SDK code style, models or error handling | "which model_config for a response model", "how errors reach the caller" | .ai-run/guides/standards/code-quality.md | - |
| Development | add or change an API area, service, model or test | "add a new service to the Python SDK", "write a unit test for a Node.js service" | .ai-run/guides/development.md | - |
| Git Workflow | branch, commit, open a PR or release | "name my branch", "how is a release published" | .ai-run/guides/standards/git-workflow.md | - |
| Security | handle credentials, placeholders, CI scans or a security report | "can I put a real host in a test", "why did the internal references job fail" | .ai-run/guides/security.md | - |
<!-- ai-run-init:task-classifier end -->

## Critical Rules

<!-- ai-run-init:critical-rules start -->
| Rule | Trigger | Action |
|---|---|---|
| Check Guides First | ANY task | Match request to category and load the P0 guide before searching broadly |
| Testing | "write tests" / "run tests" | ONLY then |
| Git Operations | "commit" / "push" / "PR" / "MR" | Only then; load `.ai-run/guides/standards/git-workflow.md` |
| Shell | ANY shell command | Use bash/Linux-compatible syntax |
| Add or update tests with every behaviour change | behaviour change | load `.ai-run/guides/development.md` |
| Edit the guides in this repository; keep one topic in one guide and commands only in the quality-gates guide | editing a guide | load `.ai-run/guides/quality-gates.md` |
| Never publish a package by hand; releases go through a GitHub Release | release or publish | load `.ai-run/guides/standards/git-workflow.md` |
| No credentials, private hostnames, personal paths or real ticket keys in any file; use placeholders | any file edit | load `.ai-run/guides/security.md` |
| Run the gates for each SDK you changed before you open a PR; the composite verify target is not a gate | before opening a PR | load `.ai-run/guides/quality-gates.md` |
| Use Conventional Commits and keep ticket keys out of branches, commits, PR titles and PR bodies | branch, commit or PR | load `.ai-run/guides/standards/git-workflow.md` |
| When you add an API area to one SDK, check whether the other SDK needs it | adding an API area | load `.ai-run/guides/architecture.md` |
<!-- ai-run-init:critical-rules end -->

## Commands

<!-- ai-run-init:commands start -->
| Need | Source Guide | Source Evidence | Notes |
|---|---|---|---|
| lint-python | .ai-run/guides/quality-gates.md | .github/workflows/ci.yml::jobs.python | Load guide before running |
| format-python | .ai-run/guides/quality-gates.md | .github/workflows/ci.yml::jobs.python | Load guide before running |
| test-python | .ai-run/guides/quality-gates.md | sdk/codemie-python/Makefile::test | Load guide before running |
| lint-nodejs | .ai-run/guides/quality-gates.md | sdk/codemie-nodejs/package.json::lint | Load guide before running |
| test-nodejs | .ai-run/guides/quality-gates.md | sdk/codemie-nodejs/package.json::test | Load guide before running |
| Git / review workflow | .ai-run/guides/standards/git-workflow.md | git history and project context | Load guide before git operations |
<!-- ai-run-init:commands end -->
