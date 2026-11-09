"""Export service — the public IaC export endpoint (GET /v1/export/{kind}/{id})."""

import requests

from ..utils import ApiRequestHandler, TokenSource


class ExportService:
    """Service for exporting a CodeMie entity as a canonical IaC document.

    The document is `{version, meta: {kind, name}, spec}`: no platform ids, credentials
    replaced with `env:` references, and references to other entities rendered by name.
    """

    def __init__(self, api_domain: str, token: TokenSource, verify_ssl: bool = True):
        """Initialize the export service.

        Args:
            api_domain: Base URL for the CodeMie API
            token: Authentication token
            verify_ssl: Whether to verify SSL certificates
        """
        self._api = ApiRequestHandler(api_domain, token, verify_ssl)

    def export(self, kind: str, entity_id: str) -> dict:
        """Export an entity as a canonical document.

        Args:
            kind: Entity kind (assistant, workflow, datasource, integration, skill, category)
            entity_id: Id of the entity to export

        Returns:
            The raw document: `{"version": ..., "meta": {"kind": ..., "name": ...}, "spec": {...}}`

        Raises:
            requests.HTTPError: non-2xx response — 404 for an unknown kind or a missing entity,
                403 for a referenced entity the caller cannot read, 422 for stored data the
                document format cannot represent (an unresolved credential or reference).
        """
        return self._api.get(
            f"/v1/export/{kind}/{entity_id}", dict, wrap_response=False
        )

    def export_raw(self, kind: str, entity_id: str) -> bytes:
        """Export an entity, returning the exact response bytes (key order, spacing) as sent.

        Use this instead of `export()` when the byte-for-byte shape of the document itself is
        under test (e.g. determinism of the canonical serialisation); `export()` parses the body
        into a dict, which loses key order.

        Raises:
            requests.HTTPError: same as `export()`.
        """
        response = self._api.get(
            f"/v1/export/{kind}/{entity_id}", requests.Response, wrap_response=False
        )
        return response.content
