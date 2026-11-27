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

"""Credential key and select-option enums for integration types.

Each ``<Type>Keys`` enum lists the credential keys the platform accepts for an
integration type, and each ``<Type><KeyName>Options`` enum lists the stored
values of a select field. Members are ``StrEnum`` members, so ``str()``, f-strings and JSON all give the
plain value and ``CredentialValues.key`` stays a ``str``.

Two registries map enums to integration types: ``KEY_ENUMS`` and
``OPTION_ENUMS``. A test compares them with a committed snapshot of the
backend's key sets (``tests/data/credential_snapshot.json``); it does not query
a live platform.

Export decision: all enums and both registries are re-exported from
``codemie_sdk``. The module stays single-file while it is under ~800 lines.
"""

from collections.abc import Mapping
from enum import Enum, StrEnum
from types import MappingProxyType

from .integration import CredentialTypes


class JiraKeys(StrEnum):
    """Credential keys of the Jira integration."""

    URL = "url"
    USERNAME = "username"
    TOKEN = "token"
    CLOUD = "cloud"
    AUTH_TYPE = "auth_type"


class ConfluenceKeys(StrEnum):
    """Credential keys of the Confluence integration."""

    URL = "url"
    USERNAME = "username"
    TOKEN = "token"
    CLOUD = "cloud"
    AUTH_TYPE = "auth_type"


class GitKeys(StrEnum):
    """Credential keys of the Git integration."""

    AUTH_TYPE = "auth_type"
    URL = "url"
    TOKEN = "token"
    APP_ID = "app_id"
    PRIVATE_KEY = "private_key"
    INSTALLATION_ID = "installation_id"


class KubernetesKeys(StrEnum):
    """Credential keys of the Kubernetes integration."""

    URL = "url"
    TOKEN = "token"
    VERIFY_SSL = "verify_ssl"


class AwsKeys(StrEnum):
    """Credential keys of the AWS integration."""

    REGION = "region"
    ACCESS_KEY_ID = "access_key_id"
    SECRET_ACCESS_KEY = "secret_access_key"
    SESSION_TOKEN = "session_token"


class GcpKeys(StrEnum):
    """Credential keys of the GCP integration."""

    SERVICE_ACCOUNT_KEY = "service_account_key"


class KeycloakKeys(StrEnum):
    """Credential keys of the Keycloak integration."""

    BASE_URL = "base_url"
    REALM = "realm"
    CLIENT_ID = "client_id"
    CLIENT_SECRET = "client_secret"
    TIMEOUT = "timeout"


class AzureKeys(StrEnum):
    """Credential keys of the Azure integration."""

    SUBSCRIPTION_ID = "subscription_id"
    TENANT_ID = "tenant_id"
    CLIENT_ID = "client_id"
    CLIENT_SECRET = "client_secret"


class ElasticKeys(StrEnum):
    """Credential keys of the Elastic integration."""

    URL = "url"
    API_KEY = "api_key"


class OpenApiKeys(StrEnum):
    """Credential keys of the OpenAPI integration."""

    SPEC = "spec"
    IS_BASIC_AUTH = "is_basic_auth"
    USERNAME = "username"
    API_KEY = "api_key"
    TIMEOUT = "timeout"
    AUTH_HEADER_NAME = "auth_header_name"


class EmailKeys(StrEnum):
    """Credential keys of the Email integration."""

    URL = "url"
    AUTH_TYPE = "auth_type"
    SMTP_USERNAME = "smtp_username"
    SMTP_PASSWORD = "smtp_password"
    OAUTH_FROM_EMAIL = "oauth_from_email"
    OAUTH_CLIENT_ID = "oauth_client_id"
    OAUTH_CLIENT_SECRET = "oauth_client_secret"
    OAUTH_TENANT_ID = "oauth_tenant_id"
    OAUTH_AUTHORITY = "oauth_authority"
    OAUTH_SCOPE = "oauth_scope"


class AzureDevOpsKeys(StrEnum):
    """Credential keys of the AzureDevOps integration."""

    URL = "url"
    TOKEN = "token"
    ORGANIZATION_URL = "organization_url"
    PROJECT = "project"
    LIMIT = "limit"
    ORGANIZATION = "organization"
    API_VERSION = "api_version"


class SonarKeys(StrEnum):
    """Credential keys of the Sonar integration."""

    URL = "url"
    TOKEN = "token"
    SONAR_PROJECT_NAME = "sonar_project_name"


class SqlKeys(StrEnum):
    """Credential keys of the SQL integration."""

    DIALECT = "dialect"
    HOST = "host"
    PORT = "port"
    USERNAME = "username"
    PASSWORD = "password"
    DATABASE_NAME = "database_name"
    TOKEN = "token"
    ORG = "org"
    BUCKET = "bucket"
    VERIFY_SSL = "verify_ssl"


class TelegramKeys(StrEnum):
    """Credential keys of the Telegram integration."""

    BOT_TOKEN = "bot_token"


class ZephyrScaleKeys(StrEnum):
    """Credential keys of the ZephyrScale integration."""

    URL = "url"
    TOKEN = "token"


class ServiceNowKeys(StrEnum):
    """Credential keys of the ServiceNow integration."""

    URL = "url"
    API_KEY = "api_key"


class ReportPortalKeys(StrEnum):
    """Credential keys of the ReportPortal integration."""

    URL = "url"
    API_KEY = "api_key"
    PROJECT = "project"


class XrayKeys(StrEnum):
    """Credential keys of the Xray integration."""

    BASE_URL = "base_url"
    CLIENT_ID = "client_id"
    CLIENT_SECRET = "client_secret"
    LIMIT = "limit"
    VERIFY_SSL = "verify_ssl"
    TIMEOUT = "timeout"


class SharePointKeys(StrEnum):
    """Credential keys of the SharePoint integration."""

    URL = "url"
    AUTH_TYPE = "auth_type"
    TENANT_ID = "tenant_id"
    CLIENT_ID = "client_id"
    CLIENT_SECRET = "client_secret"


class XWikiKeys(StrEnum):
    """Credential keys of the XWiki integration."""

    URL = "url"
    USERNAME = "username"
    TOKEN = "token"
    USE_BEARER = "use_bearer"


class ExchangeKeys(StrEnum):
    """Credential keys of the MSExchange integration."""

    AUTH_TYPE = "auth_type"
    MAILBOX = "mailbox"
    EWS_URL = "ews_url"
    SERVICE_ACCOUNT_USERNAME = "service_account_username"
    SERVICE_ACCOUNT_PASSWORD = "service_account_password"
    OAUTH_TENANT_ID = "oauth_tenant_id"
    OAUTH_CLIENT_ID = "oauth_client_id"
    OAUTH_CLIENT_SECRET = "oauth_client_secret"


class SchedulerKeys(StrEnum):
    """Credential keys of the Scheduler integration."""

    IS_ENABLED = "is_enabled"
    SCHEDULE = "schedule"
    TIMEZONE = "timezone"
    RESOURCE_TYPE = "resource_type"
    RESOURCE_ID = "resource_id"
    PROMPT = "prompt"


class WebhookKeys(StrEnum):
    """Credential keys of the Webhook integration."""

    WEBHOOK_ID = "webhook_id"
    IS_ENABLED = "is_enabled"
    SECURE_HEADER_NAME = "secure_header_name"
    SECURE_HEADER_VALUE = "secure_header_value"
    GITHUB_WEBHOOK_SECRET = "github_webhook_secret"
    GITHUB_EVENT_FILTER = "github_event_filter"
    GITHUB_REQUIRE_SHA256 = "github_require_sha256"
    GITLAB_WEBHOOK_TOKEN = "gitlab_webhook_token"
    GITLAB_FILTER_MR_ACTIONS = "gitlab_filter_mr_actions"
    GITLAB_EVENT_FILTER = "gitlab_event_filter"
    RESOURCE_TYPE = "resource_type"
    RESOURCE_ID = "resource_id"


class PluginKeys(StrEnum):
    """Credential keys of the Plugin integration."""

    PLUGIN_KEY = "plugin_key"


class FileSystemKeys(StrEnum):
    """Credential keys of the FileSystem integration."""

    ROOT_DIRECTORY = "root_directory"
    ACTIVATE_COMMAND = "activate_command"


class DialKeys(StrEnum):
    """Credential keys of the DIAL integration."""

    URL = "url"
    API_KEY = "api_key"
    API_VERSION = "api_version"


class A2aKeys(StrEnum):
    """Credential keys of the A2A integration."""

    AUTH_TYPE = "auth_type"
    AUTH_VALUE = "auth_value"
    HEADER_NAME = "header_name"
    USERNAME = "username"
    PASSWORD = "password"
    AWS_REGION = "aws_region"
    AWS_ACCESS_KEY_ID = "aws_access_key_id"
    AWS_SECRET_ACCESS_KEY = "aws_secret_access_key"
    AWS_SESSION_TOKEN = "aws_session_token"
    AWS_SERVICE_NAME = "aws_service_name"


class LiteLlmKeys(StrEnum):
    """Credential keys of the LiteLLM integration."""

    API_KEY = "api_key"
    URL = "url"


class MsTeamsKeys(StrEnum):
    """Credential keys of the MSTeams integration."""

    ASSISTANT_IDS = "assistant_ids"


class ConfluenceAuthTypeOptions(StrEnum):
    """Stored values of the Confluence ``auth_type`` select."""

    PAT = "pat"
    OAUTH = "oauth"


class JiraAuthTypeOptions(StrEnum):
    """Stored values of the Jira ``auth_type`` select."""

    PAT = "pat"
    OAUTH = "oauth"


class A2aAuthTypeOptions(StrEnum):
    """Stored values of the A2A ``auth_type`` select."""

    APIKEY = "apikey"
    BASIC = "basic"
    BEARER = "bearer"
    AWS_SIGNATURE = "aws_signature"


class EmailAuthTypeOptions(StrEnum):
    """Stored values of the Email ``auth_type`` select."""

    BASIC = "basic"
    OAUTH_AZURE = "oauth_azure"


class GitAuthTypeOptions(StrEnum):
    """Stored values of the Git ``auth_type`` select."""

    PAT = "pat"
    GITHUB_APP = "github_app"


class ExchangeAuthTypeOptions(StrEnum):
    """Stored values of the MSExchange ``auth_type`` select."""

    OAUTH_AZURE = "oauth_azure"
    NTLM = "ntlm"


class SchedulerResourceTypeOptions(StrEnum):
    """Stored values of the Scheduler ``resource_type`` select."""

    ASSISTANT = "assistant"
    WORKFLOW = "workflow"
    DATASOURCE = "datasource"


class SharePointAuthTypeOptions(StrEnum):
    """Stored values of the SharePoint ``auth_type`` select."""

    APP = "app"
    OAUTH = "oauth"


class SqlDialectOptions(StrEnum):
    """Stored values of the SQL ``dialect`` select."""

    MYSQL = "mysql"
    POSTGRES = "postgres"
    INFLUXDB = "influxdb"
    MSSQL = "mssql"


class WebhookGitlabEventFilterOptions(StrEnum):
    """Stored values of the Webhook ``gitlab_event_filter`` select."""

    OPEN = "open"
    UPDATE = "update"
    CLOSE = "close"
    REOPEN = "reopen"
    MERGE = "merge"
    APPROVED_UNAPPROVED = "approved,unapproved"


class WebhookResourceTypeOptions(StrEnum):
    """Stored values of the Webhook ``resource_type`` select."""

    ASSISTANT = "assistant"
    WORKFLOW = "workflow"
    DATASOURCE = "datasource"


KEY_ENUMS: Mapping[CredentialTypes, type[Enum]] = MappingProxyType(
    {
        CredentialTypes.JIRA: JiraKeys,
        CredentialTypes.CONFLUENCE: ConfluenceKeys,
        CredentialTypes.GIT: GitKeys,
        CredentialTypes.KUBERNETES: KubernetesKeys,
        CredentialTypes.AWS: AwsKeys,
        CredentialTypes.GCP: GcpKeys,
        CredentialTypes.KEYCLOAK: KeycloakKeys,
        CredentialTypes.AZURE: AzureKeys,
        CredentialTypes.ELASTIC: ElasticKeys,
        CredentialTypes.OPENAPI: OpenApiKeys,
        CredentialTypes.EMAIL: EmailKeys,
        CredentialTypes.AZURE_DEVOPS: AzureDevOpsKeys,
        CredentialTypes.SONAR: SonarKeys,
        CredentialTypes.SQL: SqlKeys,
        CredentialTypes.TELEGRAM: TelegramKeys,
        CredentialTypes.ZEPHYR_SCALE: ZephyrScaleKeys,
        CredentialTypes.SERVICE_NOW: ServiceNowKeys,
        CredentialTypes.REPORT_PORTAL: ReportPortalKeys,
        CredentialTypes.XRAY: XrayKeys,
        CredentialTypes.SHAREPOINT: SharePointKeys,
        CredentialTypes.XWIKI: XWikiKeys,
        CredentialTypes.MS_EXCHANGE: ExchangeKeys,
        CredentialTypes.SCHEDULER: SchedulerKeys,
        CredentialTypes.WEBHOOK: WebhookKeys,
        CredentialTypes.PLUGIN: PluginKeys,
        CredentialTypes.FILESYSTEM: FileSystemKeys,
        CredentialTypes.DIAL: DialKeys,
        CredentialTypes.A2A: A2aKeys,
        CredentialTypes.LITE_LLM: LiteLlmKeys,
        CredentialTypes.MS_TEAMS: MsTeamsKeys,
    }
)

OPTION_ENUMS: Mapping[tuple[CredentialTypes, str], type[Enum]] = MappingProxyType(
    {
        (CredentialTypes.A2A, "auth_type"): A2aAuthTypeOptions,
        (CredentialTypes.CONFLUENCE, "auth_type"): ConfluenceAuthTypeOptions,
        (CredentialTypes.JIRA, "auth_type"): JiraAuthTypeOptions,
        (CredentialTypes.EMAIL, "auth_type"): EmailAuthTypeOptions,
        (CredentialTypes.GIT, "auth_type"): GitAuthTypeOptions,
        (CredentialTypes.MS_EXCHANGE, "auth_type"): ExchangeAuthTypeOptions,
        (CredentialTypes.SCHEDULER, "resource_type"): SchedulerResourceTypeOptions,
        (CredentialTypes.SHAREPOINT, "auth_type"): SharePointAuthTypeOptions,
        (CredentialTypes.SQL, "dialect"): SqlDialectOptions,
        (
            CredentialTypes.WEBHOOK,
            "gitlab_event_filter",
        ): WebhookGitlabEventFilterOptions,
        (CredentialTypes.WEBHOOK, "resource_type"): WebhookResourceTypeOptions,
    }
)
