# Architecture

Two independent SDKs with the same shape: a client object that owns the HTTP session and one service class per API area.

## Python SDK (`sdk/codemie-python/src/codemie_sdk`)

| Path | Role |
|------|------|
| `__init__.py` | Public exports of the package |
| `client/client.py` | Client class. Picks the auth mode (Keycloak, or local auth when the API domain looks like localhost) and exposes one attribute per service; each service builds its own `ApiRequestHandler` |
| `auth/credentials.py` | Credentials and token handling |
| `services/` | One module per API area (assistant, datasource, workflow, integration, user, skill, analytics, and others) |
| `models/` | Pydantic models for requests and responses, one module per API area |
| `builders/workflow/` | Fluent builder for workflow definitions (`builder.py`, `definition.py`, `publish.py`) |
| `utils/http.py` | Shared HTTP request helper |
| `exceptions.py` | SDK exception types; no SDK code raises them and `codemie_sdk` does not export them (HTTP failures surface as `requests.HTTPError`) |

Tests: `sdk/codemie-python/tests/` (pytest, configured in `pytest.ini`).

## Node.js SDK (`sdk/codemie-nodejs/src`)

| Path | Role |
|------|------|
| `index.ts` | Public exports of the package |
| `client/client.ts` | Client class |
| `auth/` | Credentials and auth types |
| `services/` | One module per API area; file names follow the Python SDK except `category.ts` (Python `categories.py`) |
| `models/` | TypeScript types per API area |
| `schemas/` | zod schemas that validate caller parameters before a request; responses are mapped by `mappers/`, not parsed against these schemas |
| `mappers/` | Mapping between API data and SDK types |
| `exceptions/` | SDK error types |
| `utils/` | HTTP helper (`http.ts`) and small helpers (`helpers.ts`) |

Tests: `sdk/codemie-nodejs/tests/unit/` (jest, `jest.config.mjs`) and `sdk/codemie-nodejs/tests/e2e/` (live platform, `jest.e2e.config.mjs`). Build output goes through `tsup` to CJS, ESM and type declarations. Lint and format use Biome (`biome.json`).

## Parity

The two SDKs mirror the same platform API but are not generated from each other. The Python SDK has more areas today (for example `builders/workflow`, vendor services, admin). When you add an API area to one SDK, check whether the other needs it.

## Related repositories

The platform backend, the UI, the test harness and the infrastructure code are separate repositories. A change to a platform catalog (tool names, integration types, credential types) may also need a change in the backend. This repository follows the backend; it does not drive it.
