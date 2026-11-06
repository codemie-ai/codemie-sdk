# Project Context

## Project Identity

| Field | Value | Source |
|---|---|---|
| Project name | CodeMie SDK (Python and Node.js client SDKs) | `README.md` |
| Repository/package | `codemie-ai/codemie-sdk`; packages `codemie-sdk-python` (`sdk/codemie-python`, Python 3.12, Poetry) and `codemie-sdk` (`sdk/codemie-nodejs`, TypeScript, npm) | `sdk/codemie-python/pyproject.toml`, `sdk/codemie-nodejs/package.json` |
| Project code/key | `EPMCDME` | maintainer decision |

## Work Item Tracker

| Field | Value |
|---|---|
| Provider | Jira for maintainers; GitHub Issues for external contributors |
| Key/prefix | `EPMCDME`; in examples use only the placeholder `EPMCDME-NNNNN` |

> Adapter configuration belongs exclusively in `## Ticket Adapter`. Do not duplicate adapter status or instructions in the Work Item Tracker table.

## Ticket Adapter

**Status**: configured
**Adapter**: the `codemie-jira-assistant` skill (maintainers only)
**Lookup**: ask `codemie-jira-assistant` for the ticket by key; it returns summary, description, acceptance criteria and links
**Create**: give `codemie-jira-assistant` the full story file (summary, description, acceptance criteria) and ask it to create the ticket
**Output**: the ticket key
**Comment**: post the PR URL on the ticket through `codemie-jira-assistant`

## Source Control And Review

| Field | Value |
|---|---|
| Provider | GitHub |
| Repository remote | `https://github.com/codemie-ai/codemie-sdk.git` |
| Default target branch | `main` |
| Review artifact type | PR |

## MR Adapter

**Status**: configured
**Adapter**: GitHub CLI, `gh pr create`
**Instructions**: Fill in `.github/PULL_REQUEST_TEMPLATE.md`. Title, branch and commit rules are in `.ai-run/guides/standards/git-workflow.md`. Do not put a ticket key in the title or body. External contributors close their GitHub issue with `Closes #N`.

## Complexity Scoring

**Status**: not configured
**Field**: not configured
**Format**: not configured
