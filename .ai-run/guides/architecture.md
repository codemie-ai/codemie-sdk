# Architecture

Two independent SDKs with the same shape: a client object that owns the HTTP session and one service class per API area.

## Python SDK (`sdk/codemie-python/src/codemie_sdk`)

| Path | Role |
|------|------|
| `__init__.py` | Public exports of the package |
| `client/client.py` | Client class. Builds the HTTP session and exposes one attribute per service |
| `auth/credentials.py` | Credentials and token handling |
| `services/` | One module per API area (assistant, datasource, workflow, integration, user, skill, analytics, and others) |
| `models/` | Pydantic models for requests and responses, one module per API area |
| `builders/workflow/` | Fluent builder for workflow definitions (`builder.py`, `definition.py`, `publish.py`) |
| `utils/http.py` | Shared HTTP request helper |
| `exceptions.py` | SDK exception types |

Tests: `sdk/codemie-python/tests/` (pytest, configured in `pytest.ini`).

## Node.js SDK (`sdk/codemie-nodejs/src`)

| Path | Role |
|------|------|
| `index.ts` | Public exports of the package |
| `client/client.ts` | Client class |
| `auth/` | Credentials and auth types |
| `services/` | One module per API area, same names as the Python SDK where the area exists in both |
| `models/` | TypeScript types per API area |
| `schemas/` | zod schemas that validate request and response data |
| `mappers/` | Mapping between API data and SDK types |
| `exceptions/` | SDK error types |
| `utils/` | HTTP helper (`http.ts`) and small helpers (`helpers.ts`) |

Tests: `sdk/codemie-nodejs/tests/` (jest). Build output goes through `tsup` to CJS, ESM and type declarations. Lint and format use Biome (`biome.json`).

## Parity

The two SDKs mirror the same platform API but are not generated from each other. The Python SDK has more areas today (for example `builders/workflow`, vendor services, admin). When you add an API area to one SDK, check whether the other needs it.
