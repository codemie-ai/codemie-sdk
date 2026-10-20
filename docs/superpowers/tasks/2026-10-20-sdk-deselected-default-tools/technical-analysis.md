# Technical Research (sliced from parent: component `codemie-sdk`)

**Task**: SDKs: Python, Node and IaC models carry the assistant-level list of deselected default tools
**Generated**: 2026-10-16
**Research path**: codegraph (sliced from ../../technical-analysis.md; no re-analysis)

---

## Codebase Findings

- Python SDK: `codemie_sdk/models/assistant.py` and `services/assistant.py`. The `ToolDetails` model uses `extra="ignore"`, so unknown fields are silently dropped. `AssistantService.get_tools()` returns `list[ToolKitDetails]`.
- Node SDK: `sdk/codemie-nodejs/src/models/assistant.ts`; unit tests in `sdk/codemie-nodejs/tests/unit/services/assistant.test.ts`.
- IaC Node tooling: `iac/codemie-iac-nodejs` — backup, import, converters and checksum utilities. `normalizeTool` and `transformTool` strip fields and feed checksums; a new assistant-level field must be added to normalisation, transformers and checksum input.
- Test locations: `sdk/codemie-python/tests/test_prompt_variables.py`; test harness assistant tests under `test-harness/codemie_test_harness/tests/assistant/`; IaC `backup.test.ts`, `backupTransformers.test.ts`, `converters.test.ts`, `checksumUtils.test.ts`.

## Dependencies

Depends on the backend story: the field name, semantics (empty = nothing deselected), validation errors and the tool listing contents are defined there.

## Risk Indicators

- Model drift between Python, Node and IaC models; silent field loss via `extra="ignore"` and IaC field stripping.
- An omitted field must not clear an existing deselection on update (depends on backend treatment of omitted fields).
- Checksum changes could cause IaC tooling to see all assistants as changed if the new field is added without a stable default.

## Summary for Complexity Assessment

Single-repo SDK slice (Python, Node and IaC Node packages inside `codemie-sdk`): add one assistant-level field to three model sets, create/update/read round-trip, backup/import and checksum handling, plus tests. Pattern is well established (adding a field to existing assistant models); the risk is consistency across the three packages and checksum stability.
