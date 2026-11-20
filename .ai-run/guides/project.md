# Project Context

## Project Identity

| Field | Value | Source |
|---|---|---|
| Project name | CodeMie SDK | README.md::CodeMie |
| Repository/package | codemie-ai/codemie-sdk | sdk/codemie-python/pyproject.toml::repository |
| Project code/key | EPMCDME | user decision |

## Work Item Tracker

| Field | Value |
|---|---|
| Provider | Jira |
| Key/prefix | EPMCDME |

## Ticket Adapter

**Status**: configured
**Adapter**: skill:codemie-jira-assistant
**Lookup**: Invoke the `codemie-jira-assistant` skill with the ticket key and a request for summary, description, acceptance criteria, and links.
**Create**: Invoke the `codemie-jira-assistant` skill with the complete ticket payload or approved story file as the argument.
**Output**: Ticket key and URL returned by the skill.
**Comment**: Invoke the `codemie-jira-assistant` skill with a request to add a comment to the ticket, passing the comment body as the argument.
**Instructions**: Maintainers only; external contributors use GitHub Issues and link them with `Closes #N`. The comment posted on the ticket is the PR URL. Never write the ticket key into a branch, commit, PR title or PR body.

## Source Control And Review

| Field | Value |
|---|---|
| Provider | GitHub |
| Repository remote | github |
| Default target branch | main |
| Review artifact type | PR |

## MR Adapter

**Status**: configured
**Adapter**: GitHub CLI (`gh pr create`)
**Instructions**: Fill in `.github/PULL_REQUEST_TEMPLATE.md`. Title, branch and commit rules are in `.ai-run/guides/standards/git-workflow.md`. No ticket key in the title or body; external contributors close their GitHub issue with `Closes #N`.
**Body Template**: .github/PULL_REQUEST_TEMPLATE.md

## Complexity Scoring

**Status**: not configured
**Field**: not configured
**Format**: not configured
