# Copyright 2026 EPAM Systems, Inc. ("EPAM")
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Hosted application service for the CodeMie SDK.

Wraps the management API under ``/v1/hosted-applications``. Changes to an existing
application or version carry the ``etag`` of the item as ``If-Match``; read it from the
latest answer. Every change also carries an ``Idempotency-Key``: pass one to repeat a
request safely, or leave it out to get a fresh key per call.
"""

from typing import Any
from urllib.parse import quote
from uuid import uuid4

import requests

from ..models.hosted_application import (
    HostedApplication,
    HostedApplicationCapabilities,
    HostedApplicationDeletion,
    HostedApplicationDeletionStatus,
    HostedApplicationLaunch,
    HostedApplicationList,
    HostedApplicationSharableUsers,
    HostedApplicationSharedWith,
    HostedApplicationShareLink,
    HostedApplicationShareLinkTarget,
    HostedApplicationUploadReceipt,
    HostedApplicationUsage,
    HostedApplicationValidationReport,
    HostedApplicationVersion,
    HostedApplicationVersionList,
    HostedApplicationVersionQueued,
    HostedApplicationVersionStart,
)
from ..utils import ApiRequestHandler, TokenSource

_BASE = "/v1/hosted-applications"
_ADMIN_BASE = "/v1/admin/hosted-applications"
_IF_MATCH = "If-Match"
_IDEMPOTENCY_KEY = "Idempotency-Key"
_UPLOAD_GENERATION = "X-Upload-Generation"


class HostedApplicationService:
    """Service for hosted static applications: upload, share and open.

    Every change sends an idempotency key. Without an ``idempotency_key`` argument the service
    generates a fresh one per call, so a retry after a timeout is not protected from running twice
    (for example, a second application is created). A caller that retries must generate one key
    and pass the same value on every attempt.
    """

    def __init__(self, api_domain: str, token: TokenSource, verify_ssl: bool = True):
        """Initialize the hosted application service.

        Args:
            api_domain: Base URL for the CodeMie API
            token: Authentication token
            verify_ssl: Whether to verify SSL certificates
        """
        self._api_domain = api_domain.rstrip("/")
        self._verify_ssl = verify_ssl
        self._api = ApiRequestHandler(self._api_domain, token, verify_ssl)

    def with_token(self, token: TokenSource) -> "HostedApplicationService":
        """Return a service for the same API that authenticates with another token.

        Args:
            token: Authentication token, for example the token of a service account

        Returns:
            A new HostedApplicationService; this one is left unchanged
        """
        return HostedApplicationService(self._api_domain, token, self._verify_ssl)

    @staticmethod
    def _path(*parts: str) -> str:
        return "/".join([_BASE, *(quote(str(part), safe="") for part in parts)])

    @staticmethod
    def _headers(
        if_match: str | None = None, idempotency_key: str | None = None
    ) -> dict[str, str]:
        headers = {_IDEMPOTENCY_KEY: idempotency_key or str(uuid4())}
        if if_match is not None:
            headers[_IF_MATCH] = if_match
        return headers

    def capabilities(self) -> HostedApplicationCapabilities:
        """What the caller may do. Accounts that cannot use the feature get ``view=False``."""
        return self._api.get(
            f"{_BASE}/capabilities", HostedApplicationCapabilities, wrap_response=False
        )

    def usage(self) -> HostedApplicationUsage:
        """Storage quota of the caller."""
        return self._api.get(
            f"{_BASE}/usage", HostedApplicationUsage, wrap_response=False
        )

    def list_applications(
        self,
        scope: str = "mine",
        q: str = "",
        limit: int = 24,
        cursor: str | None = None,
        sort: str = "updated_desc",
        **filters: Any,
    ) -> HostedApplicationList:
        """List the applications the caller may open in one scope.

        Args:
            scope: mine, project, marketplace or shared
            q: Search text over name and description
            limit: Page size, 1 to 100
            cursor: ``next_cursor`` of the previous page
            sort: updated_desc, created_desc or name_asc
            **filters: Further server filters such as ``artifact_kind``, ``project``,
                ``created_by``, ``shared`` or ``status``; unset values are not sent
        """
        params: dict[str, Any] = {
            "scope": scope,
            "q": q,
            "limit": limit,
            "sort": sort,
            **{key: value for key, value in filters.items() if value is not None},
        }
        if cursor:
            params["cursor"] = cursor
        return self._api.get(
            _BASE, HostedApplicationList, params=params, wrap_response=False
        )

    def get_application(self, app_id: str) -> HostedApplication:
        """Get one application."""
        return self._api.get(self._path(app_id), HostedApplication, wrap_response=False)

    def get_thumbnail(self, app_id: str) -> requests.Response:
        """Get the cover image of an application.

        Returns the raw response: the image bytes, or an empty 204 answer when the
        application has no cover.
        """
        return self._api.get(self._path(app_id, "thumbnail"), requests.Response)

    def create_application(
        self,
        name: str,
        description: str,
        project: str,
        shared: bool = False,
        idempotency_key: str | None = None,
    ) -> HostedApplication:
        """Create a private application, or one shared with every member of ``project``."""
        return self._api.request(
            "POST",
            _BASE,
            HostedApplication,
            json_data={
                "name": name,
                "description": description,
                "project": project,
                "shared": shared,
            },
            extra_headers=self._headers(idempotency_key=idempotency_key),
            wrap_response=False,
        )

    def delete_application(
        self, app_id: str, if_match: str, idempotency_key: str | None = None
    ) -> HostedApplicationDeletion:
        """Delete an application. Its files are purged afterwards; see ``deletion_status``."""
        return self._api.request(
            "DELETE",
            self._path(app_id),
            HostedApplicationDeletion,
            extra_headers=self._headers(if_match, idempotency_key),
            wrap_response=False,
        )

    def deletion_status(self, app_id: str) -> HostedApplicationDeletionStatus:
        """Progress of the purge of a deleted application."""
        return self._api.get(
            self._path(app_id, "deletion-status"),
            HostedApplicationDeletionStatus,
            wrap_response=False,
        )

    def start_version(
        self,
        app_id: str,
        filename: str,
        artifact_kind: str,
        byte_size: int,
        if_match: str,
        sha256: str | None = None,
        routing_mode: str = "static",
        site_root_hint: str | None = None,
        entrypoint_hint: str | None = None,
        idempotency_key: str | None = None,
    ) -> HostedApplicationVersionStart:
        """Start a new version; upload its artifact next.

        Args:
            app_id: Application id
            filename: Name of the artifact, ``.html`` or ``.zip``
            artifact_kind: html or zip
            byte_size: Size of the artifact in bytes
            if_match: ``etag`` of the application
            sha256: Hex digest the stored bytes must match, when known
            routing_mode: static or spa_history
            site_root_hint: Folder of the site inside a ZIP
            entrypoint_hint: Entry page inside a ZIP
            idempotency_key: Key to repeat the request safely
        """
        body: dict[str, Any] = {
            "filename": filename,
            "artifact_kind": artifact_kind,
            "byte_size": byte_size,
            "routing_mode": routing_mode,
        }
        for key, value in (
            ("sha256", sha256),
            ("site_root_hint", site_root_hint),
            ("entrypoint_hint", entrypoint_hint),
        ):
            if value is not None:
                body[key] = value
        return self._api.request(
            "POST",
            self._path(app_id, "versions"),
            HostedApplicationVersionStart,
            json_data=body,
            extra_headers=self._headers(if_match, idempotency_key),
            wrap_response=False,
        )

    def upload_artifact(
        self,
        app_id: str,
        version_id: str,
        content: bytes,
        upload_etag: str,
        generation: int,
    ) -> HostedApplicationUploadReceipt:
        """Send the bytes of the artifact of a started version.

        Args:
            app_id: Application id
            version_id: Version id from ``start_version``
            content: The artifact bytes
            upload_etag: ``upload_etag`` of ``start_version``
            generation: ``generation`` of ``start_version``
        """
        return self._api.request(
            "PUT",
            self._path(app_id, "versions", version_id, "artifact"),
            HostedApplicationUploadReceipt,
            data=content,
            extra_headers={
                "Content-Type": "application/octet-stream",
                _IF_MATCH: upload_etag,
                _UPLOAD_GENERATION: str(generation),
            },
            wrap_response=False,
        )

    def complete_version(
        self,
        app_id: str,
        version_id: str,
        upload_id: str,
        sha256: str,
        generation: int,
        if_match: str,
        idempotency_key: str | None = None,
    ) -> HostedApplicationVersionQueued:
        """Finish an upload and queue the version for validation.

        Args:
            app_id: Application id
            version_id: Version id
            upload_id: ``upload_id`` of ``start_version``
            sha256: Digest from the upload receipt
            generation: Generation of the upload
            if_match: ``version_etag`` of the upload receipt
            idempotency_key: Key to repeat the request safely
        """
        return self._api.request(
            "POST",
            self._path(app_id, "versions", version_id, "complete"),
            HostedApplicationVersionQueued,
            json_data={
                "generation": generation,
                "upload_id": upload_id,
                "sha256": sha256,
            },
            extra_headers=self._headers(if_match, idempotency_key),
            wrap_response=False,
        )

    def get_version(self, app_id: str, version_id: str) -> HostedApplicationVersion:
        """Get one version with its validation state."""
        return self._api.get(
            self._path(app_id, "versions", version_id),
            HostedApplicationVersion,
            wrap_response=False,
        )

    def list_versions(
        self, app_id: str, limit: int = 20, cursor: str | None = None
    ) -> HostedApplicationVersionList:
        """List the versions of an application, newest first."""
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        return self._api.get(
            self._path(app_id, "versions"),
            HostedApplicationVersionList,
            params=params,
            wrap_response=False,
        )

    def get_version_validation(
        self, app_id: str, version_id: str, offset: int = 0, limit: int = 100
    ) -> HostedApplicationValidationReport:
        """Get the validation report of a version."""
        return self._api.get(
            self._path(app_id, "versions", version_id, "validation"),
            HostedApplicationValidationReport,
            params={"offset": offset, "limit": limit},
            wrap_response=False,
        )

    def configure_version(
        self,
        app_id: str,
        version_id: str,
        site_root: str,
        entrypoint_path: str,
        routing_mode: str,
        candidate_manifest_digest: str,
        configuration_revision: int,
        if_match: str,
        idempotency_key: str | None = None,
    ) -> HostedApplicationVersionQueued:
        """Choose the site root and entry page of a version that awaits configuration.

        Take ``site_root`` and ``entrypoint_path`` from the ``roots`` and ``entries`` of
        the validation report, and the digest and revision from the same report.
        """
        return self._api.request(
            "PUT",
            self._path(app_id, "versions", version_id, "configuration"),
            HostedApplicationVersionQueued,
            json_data={
                "site_root": site_root,
                "entrypoint_path": entrypoint_path,
                "routing_mode": routing_mode,
                "candidate_manifest_digest": candidate_manifest_digest,
                "configuration_revision": configuration_revision,
            },
            extra_headers=self._headers(if_match, idempotency_key),
            wrap_response=False,
        )

    def select_version(
        self,
        app_id: str,
        version_id: str,
        if_match: str,
        idempotency_key: str | None = None,
    ) -> HostedApplication:
        """Make an accepted version the working version; the live version is untouched."""
        return self._api.request(
            "POST",
            self._path(app_id, "select-version"),
            HostedApplication,
            json_data={"version_id": version_id},
            extra_headers=self._headers(if_match, idempotency_key),
            wrap_response=False,
        )

    def activate(
        self,
        app_id: str,
        version_id: str,
        if_match: str,
        idempotency_key: str | None = None,
    ) -> HostedApplication:
        """Make an accepted version the live version that recipients open."""
        return self._api.request(
            "POST",
            self._path(app_id, "activate"),
            HostedApplication,
            json_data={"version_id": version_id},
            extra_headers=self._headers(if_match, idempotency_key),
            wrap_response=False,
        )

    def marketplace_publish(
        self, app_id: str, if_match: str, idempotency_key: str | None = None
    ) -> HostedApplication:
        """Publish an application to the marketplace."""
        return self._api.request(
            "POST",
            self._path(app_id, "marketplace", "publish"),
            HostedApplication,
            json_data={},
            extra_headers=self._headers(if_match, idempotency_key),
            wrap_response=False,
        )

    def marketplace_unpublish(
        self, app_id: str, if_match: str, idempotency_key: str | None = None
    ) -> HostedApplication:
        """Remove an application from the marketplace."""
        return self._api.request(
            "POST",
            self._path(app_id, "marketplace", "unpublish"),
            HostedApplication,
            json_data={},
            extra_headers=self._headers(if_match, idempotency_key),
            wrap_response=False,
        )

    def share_with_users(
        self, app_id: str, user_ids: list[str]
    ) -> HostedApplicationSharedWith:
        """Grant view access by name (owner only)."""
        return self._api.post(
            self._path(app_id, "share"),
            HostedApplicationSharedWith,
            json_data={"user_ids": user_ids},
            wrap_response=False,
        )

    def unshare(self, app_id: str, user_ids: list[str]) -> HostedApplicationSharedWith:
        """Revoke the view access granted by name (owner only)."""
        return self._api.delete(
            self._path(app_id, "share"),
            HostedApplicationSharedWith,
            json_data={"user_ids": user_ids},
            wrap_response=False,
        )

    def shared_with(self, app_id: str) -> HostedApplicationSharedWith:
        """People the application is shared with by name (owner only)."""
        return self._api.get(
            self._path(app_id, "shared-with"),
            HostedApplicationSharedWith,
            wrap_response=False,
        )

    def sharable_users(self, app_id: str, q: str) -> HostedApplicationSharableUsers:
        """Directory users matching ``q`` that can be granted access (owner only)."""
        return self._api.get(
            self._path(app_id, "sharable-users"),
            HostedApplicationSharableUsers,
            params={"q": q},
            wrap_response=False,
        )

    def get_share_link(self, app_id: str) -> HostedApplicationShareLink:
        """The live share link of an application, if any (owner only)."""
        return self._api.get(
            self._path(app_id, "share-link"),
            HostedApplicationShareLink,
            wrap_response=False,
        )

    def create_share_link(self, app_id: str) -> HostedApplicationShareLink:
        """Create the share link of an application, or get the live one (owner only)."""
        return self._api.post(
            self._path(app_id, "share-link"),
            HostedApplicationShareLink,
            wrap_response=False,
        )

    def delete_share_link(self, app_id: str) -> HostedApplicationShareLink:
        """Revoke the share link and the access it gave."""
        return self._api.delete(
            self._path(app_id, "share-link"),
            HostedApplicationShareLink,
            wrap_response=False,
        )

    def open_share_link(self, token: str) -> HostedApplicationShareLinkTarget:
        """Open a share link: the caller gets view access and the application id."""
        # `request` sends the body without logging it; `post` would write the token to the debug log.
        return self._api.request(
            "POST",
            f"{_BASE}/share-links/open",
            HostedApplicationShareLinkTarget,
            json_data={"token": token},
            wrap_response=False,
        )

    def launch(
        self,
        app_id: str,
        purpose: str = "published_view",
        version_id: str | None = None,
        path: str | None = None,
    ) -> HostedApplicationLaunch:
        """Get a one-use launch ticket for opening an application.

        Args:
            app_id: Application id
            purpose: published_view (the live version, for readers) or owner_preview
                (the working version, for managers)
            version_id: Version to open, for an owner preview
            path: Page of the version to open; the entry page when omitted
        """
        body: dict[str, Any] = {"purpose": purpose}
        if version_id is not None:
            body["version_id"] = version_id
        if path is not None:
            body["path"] = path
        return self._api.post(
            self._path(app_id, "launch"),
            HostedApplicationLaunch,
            json_data=body,
            wrap_response=False,
        )

    def suspend_application(
        self,
        app_id: str,
        reason: str,
        if_match: str | None = None,
        idempotency_key: str | None = None,
    ) -> HostedApplication:
        """Take an application down at once (platform administrators only)."""
        return self._security(
            app_id, "suspend", {"reason": reason}, if_match, idempotency_key
        )

    def reinstate_application(
        self,
        app_id: str,
        reason: str,
        if_match: str,
        version_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> HostedApplication:
        """Bring a suspended application back (an administrator other than its creator)."""
        body: dict[str, Any] = {"reason": reason}
        if version_id is not None:
            body["version_id"] = version_id
        return self._security(app_id, "reinstate", body, if_match, idempotency_key)

    def _security(
        self,
        app_id: str,
        action: str,
        body: dict[str, Any],
        if_match: str | None,
        idempotency_key: str | None,
    ) -> HostedApplication:
        return self._api.request(
            "POST",
            f"{_ADMIN_BASE}/{quote(str(app_id), safe='')}/security/{action}",
            HostedApplication,
            json_data=body,
            extra_headers=self._headers(if_match, idempotency_key),
            wrap_response=False,
        )
