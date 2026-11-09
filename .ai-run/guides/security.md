# Security

Sources: `SECURITY.md` (reporting policy) and `CONTRIBUTING.md`, section "Internal References and Secrets".

## Rules for contributors

- Never commit credentials, tokens, private hostnames, internal ticket keys, or personal e-mail addresses or paths.
- Use placeholders in examples and tests, for example `https://your-codemie-host.example.com`. For ticket keys use `EPMCDME-NNNNN`.
- Read API keys and tokens from environment variables or a secret store, never from source.
- Do not disable TLS certificate checks in SDK code, examples or tests.
- Do not log credentials, tokens or full request headers.

## CI scans

Two jobs in `.github/workflows/ci.yml` block a PR:

- "Internal references" (job `internal-refs`) scans the tree for internal references.
- "Security" (job `secrets-detection`) scans for secrets. Its local rules are in `.gitleaks.toml`.

Check your own diff before you push. Guide files in `.ai-run/guides` and `docs` are scanned too.

## Reporting a vulnerability

Do not open a public issue. Use the GitHub Security Advisory feature, as `SECURITY.md` describes. Do not put real credentials or customer data in a report.
