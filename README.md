<div align="center">

<img src="assets/codemie-logo.svg" alt="CodeMie" width="96" />

# CodeMie SDK

**Official Python and TypeScript client SDKs for the CodeMie platform.**

[![PyPI](https://img.shields.io/pypi/v/codemie-sdk-python.svg?style=flat-square&label=PyPI)](https://pypi.org/project/codemie-sdk-python/)
[![npm](https://img.shields.io/npm/v/codemie-sdk.svg?style=flat-square&label=npm)](https://www.npmjs.com/package/codemie-sdk)
[![CI](https://img.shields.io/github/actions/workflow/status/codemie-ai/codemie-sdk/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/codemie-ai/codemie-sdk/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg?style=flat-square)](#requirements)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=flat-square)](LICENSE)

</div>

## What is it

[CodeMie](https://github.com/codemie-ai/codemie-code) is an AI platform for building and running assistants and workflows. This repository holds the client libraries for its API. Use them to create and run assistants, workflows and datasources, call LLMs and manage integrations from your own code.

- **Two languages, one API surface.** The Python and TypeScript / Node.js clients cover the same CodeMie services.
- **Full platform coverage.** Assistants, workflows, datasources, integrations, conversations, files, users and more.
- **Flexible authentication.** Client credentials, username and password, or an SSO cookie.

| SDK | Language | Documentation |
|-----|----------|---------------|
| `sdk/codemie-python` | Python | [Python SDK README](sdk/codemie-python/README.md) |
| `sdk/codemie-nodejs` | TypeScript / JavaScript (Node.js) | [Node.js SDK README](sdk/codemie-nodejs/README.md) |

## Installation

```bash
pip install codemie-sdk-python
npm install codemie-sdk
```

## Related repositories

- [codemie-cdk](https://github.com/codemie-ai/codemie-cdk): infrastructure as code for CodeMie assistants, datasources and workflows.
- [codemie-mcp-servers](https://github.com/codemie-ai/codemie-mcp-servers): MCP servers that give AI tools access to CodeMie.

## Quick start

Python:

```python
from codemie_sdk import CodeMieClient

client = CodeMieClient(
    auth_server_url="https://your-keycloak-host.example.com/auth",
    auth_client_id="your-client-id",
    auth_client_secret="your-client-secret",
    auth_realm_name="your-realm",
    codemie_api_domain="https://your-codemie-host.example.com/code-assistant-api",
)
```

Node.js:

```typescript
import { CodeMieClient } from 'codemie-sdk';

const client = new CodeMieClient({
  auth_server_url: 'https://your-keycloak-host.example.com/auth',
  auth_realm_name: 'your-realm',
  codemie_api_domain: 'https://your-codemie-host.example.com/code-assistant-api',
  username: process.env.USERNAME,
  password: process.env.PASSWORD,
});
await client.initialize();
```

Each SDK README lists every service and method.

## Requirements

- Python 3.12 or later (`codemie-sdk-python`)
- A CodeMie installation to connect to

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md) first.

## Security

Do not report vulnerabilities in public issues. Follow [SECURITY.md](SECURITY.md).

For bugs and feature requests, use [GitHub Issues](https://github.com/codemie-ai/codemie-sdk/issues).

## Releasing

See [docs/RELEASING.md](docs/RELEASING.md).

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE).
