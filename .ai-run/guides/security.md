# Security

Sources: `SECURITY.md` (reporting policy) and `CONTRIBUTING.md`, section "Internal References and Secrets".

## Rules for contributors

- Never commit credentials, tokens, private hostnames, internal ticket keys, or personal e-mail addresses or paths.
- Use placeholders in examples and tests, for example `https://your-codemie-host.example.com`. For ticket keys use `EPMCDME-NNNNN`.
- Read API keys and tokens from environment variables or a secret store, never from source.
- Do not disable TLS certificate checks in SDK code, examples or tests.
  - Known debt, to fix: `sdk/codemie-nodejs/tests/unit/utils/http.test.ts` (constructs `ApiRequestHandler` with `verifySSL: false`), `sdk/codemie-python/src/codemie_sdk/client/client.py` (silences `InsecureRequestWarning` when `verify_ssl` is False), `sdk/codemie-python/pytest.ini` (ignores `InsecureRequestWarning`).
- Do not log credentials, tokens or full request headers.
  - Known debt, to fix: `sdk/codemie-python/src/codemie_sdk/utils/http.py` (`post`, `put`, `patch` log the full JSON body at DEBUG, so `IntegrationService.create` / `update` credentials reach the log).

## CI scans

Two jobs in `.github/workflows/ci.yml` run on every PR and on every push to `main`:

- "Internal references" (job `internal-refs`) runs `scan_internal_refs.py` from `codemie-ai/ci-workflows` over the checked-out tree. It fails on an internal e-mail domain, an internal host, a ticket key followed by digits, or the production realm name; the `EPMCDME-NNNNN` placeholder does not match.
- "Security" (job `secrets-detection`) runs gitleaks through the `codemie-ai/ci-workflows` reusable workflow. `.gitleaks.toml` extends the default gitleaks rules and allowlists three stopwords.

Check your own diff before you push. Guide files in `.ai-run/guides` and `docs` are scanned too.

## Reporting a vulnerability

Do not open a public issue. Use the GitHub Security Advisory feature, as `SECURITY.md` describes. Do not put real credentials or customer data in a report.
