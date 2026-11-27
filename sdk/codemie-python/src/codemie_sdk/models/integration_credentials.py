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
values of a select field. Members are ``str`` enums, so they serialize exactly
like plain strings and ``CredentialValues.key`` stays a ``str``.

Two registries map enums to integration types: ``KEY_ENUMS`` and
``OPTION_ENUMS``. A drift test compares them with a committed snapshot of the
platform's key sets (``tests/data/credential_snapshot.json``).

Export decision: all enums and both registries are re-exported from
``codemie_sdk``. The module stays single-file while it is under ~800 lines.
"""

from enum import Enum

from .integration import CredentialTypes


class JiraKeys(str, Enum):
    """Credential keys of the Jira integration."""

    URL = "url"
    USERNAME = "username"
    TOKEN = "token"
    CLOUD = "cloud"
    AUTH_TYPE = "auth_type"


class ConfluenceKeys(str, Enum):
    """Credential keys of the Confluence integration."""

    URL = "url"
    USERNAME = "username"
    TOKEN = "token"
    CLOUD = "cloud"
    AUTH_TYPE = "auth_type"


class GitKeys(str, Enum):
    """Credential keys of the Git integration."""

    AUTH_TYPE = "auth_type"
    URL = "url"
    TOKEN = "token"
    APP_ID = "app_id"
    PRIVATE_KEY = "private_key"
    INSTALLATION_ID = "installation_id"


class KubernetesKeys(str, Enum):
    """Credential keys of the Kubernetes integration."""

    URL = "url"
    TOKEN = "token"
    VERIFY_SSL = "verify_ssl"


class AwsKeys(str, Enum):
    """Credential keys of the AWS integration."""

    REGION = "region"
    ACCESS_KEY_ID = "access_key_id"
    SECRET_ACCESS_KEY = "secret_access_key"
    SESSION_TOKEN = "session_token"


class GcpKeys(str, Enum):
    """Credential keys of the GCP integration."""

    SERVICE_ACCOUNT_KEY = "service_account_key"


class KeycloakKeys(str, Enum):
    """Credential keys of the Keycloak integration."""

    BASE_URL = "base_url"
    REALM = "realm"
    CLIENT_ID = "client_id"
    CLIENT_SECRET = "client_secret"
    TIMEOUT = "timeout"


class AzureKeys(str, Enum):
    """Credential keys of the Azure integration."""

    SUBSCRIPTION_ID = "subscription_id"
    TENANT_ID = "tenant_id"
    CLIENT_ID = "client_id"
    CLIENT_SECRET = "client_secret"


class ElasticKeys(str, Enum):
    """Credential keys of the Elastic integration."""

    URL = "url"
    API_KEY = "api_key"


class OpenApiKeys(str, Enum):
    """Credential keys of the OpenAPI integration."""

    SPEC = "spec"
    IS_BASIC_AUTH = "is_basic_auth"
    USERNAME = "username"
    API_KEY = "api_key"
    TIMEOUT = "timeout"
    AUTH_HEADER_NAME = "auth_header_name"


class EmailKeys(str, Enum):
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


class AzureDevOpsKeys(str, Enum):
    """Credential keys of the AzureDevOps integration."""

    URL = "url"
    TOKEN = "token"
    ORGANIZATION_URL = "organization_url"
    PROJECT = "project"
    LIMIT = "limit"
    ORGANIZATION = "organization"
    API_VERSION = "api_version"


class SonarKeys(str, Enum):
    """Credential keys of the Sonar integration."""

    URL = "url"
    TOKEN = "token"
    SONAR_PROJECT_NAME = "sonar_project_name"


class SqlKeys(str, Enum):
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


class TelegramKeys(str, Enum):
    """Credential keys of the Telegram integration."""

    BOT_TOKEN = "bot_token"


class ZephyrScaleKeys(str, Enum):
    """Credential keys of the ZephyrScale integration."""

    URL = "url"
    TOKEN = "token"


class ServiceNowKeys(str, Enum):
    """Credential keys of the ServiceNow integration."""

    URL = "url"
    API_KEY = "api_key"


class ReportPortalKeys(str, Enum):
    """Credential keys of the ReportPortal integration."""

    URL = "url"
    API_KEY = "api_key"
    PROJECT = "project"


class XrayKeys(str, Enum):
    """Credential keys of the Xray integration."""

    BASE_URL = "base_url"
    CLIENT_ID = "client_id"
    CLIENT_SECRET = "client_secret"
    LIMIT = "limit"
    VERIFY_SSL = "verify_ssl"
    TIMEOUT = "timeout"


class SharePointKeys(str, Enum):
    """Credential keys of the SharePoint integration."""

    URL = "url"
    AUTH_TYPE = "auth_type"
    TENANT_ID = "tenant_id"
    CLIENT_ID = "client_id"
    CLIENT_SECRET = "client_secret"


class XWikiKeys(str, Enum):
    """Credential keys of the XWiki integration."""

    URL = "url"
    USERNAME = "username"
    TOKEN = "token"
    USE_BEARER = "use_bearer"


class ExchangeKeys(str, Enum):
    """Credential keys of the MSExchange integration."""

    AUTH_TYPE = "auth_type"
    MAILBOX = "mailbox"
    EWS_URL = "ews_url"
    SERVICE_ACCOUNT_USERNAME = "service_account_username"
    SERVICE_ACCOUNT_PASSWORD = "service_account_password"
    OAUTH_TENANT_ID = "oauth_tenant_id"
    OAUTH_CLIENT_ID = "oauth_client_id"
    OAUTH_CLIENT_SECRET = "oauth_client_secret"


class A2aAuthTypeOptions(str, Enum):
    """Stored values of the A2A ``auth_type`` select."""

    APIKEY = "apikey"
    BASIC = "basic"
    BEARER = "bearer"
    AWS_SIGNATURE = "aws_signature"


class EmailAuthTypeOptions(str, Enum):
    """Stored values of the Email ``auth_type`` select."""

    BASIC = "basic"
    OAUTH_AZURE = "oauth_azure"


class GitAuthTypeOptions(str, Enum):
    """Stored values of the Git ``auth_type`` select."""

    PAT = "pat"
    GITHUB_APP = "github_app"


class ExchangeAuthTypeOptions(str, Enum):
    """Stored values of the MSExchange ``auth_type`` select."""

    OAUTH_AZURE = "oauth_azure"
    NTLM = "ntlm"


class SchedulerResourceTypeOptions(str, Enum):
    """Stored values of the Scheduler ``resource_type`` select."""

    ASSISTANT = "assistant"
    WORKFLOW = "workflow"
    DATASOURCE = "datasource"


class SharePointAuthTypeOptions(str, Enum):
    """Stored values of the SharePoint ``auth_type`` select."""

    APP = "app"
    OAUTH = "oauth"


class SqlDialectOptions(str, Enum):
    """Stored values of the SQL ``dialect`` select."""

    MYSQL = "mysql"
    POSTGRES = "postgres"
    INFLUXDB = "influxdb"
    MSSQL = "mssql"


class WebhookGitlabEventFilterOptions(str, Enum):
    """Stored values of the Webhook ``gitlab_event_filter`` select."""

    OPEN = "open"
    UPDATE = "update"
    CLOSE = "close"
    REOPEN = "reopen"
    MERGE = "merge"
    APPROVED_UNAPPROVED = "approved,unapproved"


class WebhookResourceTypeOptions(str, Enum):
    """Stored values of the Webhook ``resource_type`` select."""

    ASSISTANT = "assistant"
    WORKFLOW = "workflow"
    DATASOURCE = "datasource"


KEY_ENUMS: dict[CredentialTypes, type[Enum]] = {
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
}

OPTION_ENUMS: dict[tuple[CredentialTypes, str], type[Enum]] = {
    (CredentialTypes.A2A, "auth_type"): A2aAuthTypeOptions,
    (CredentialTypes.EMAIL, "auth_type"): EmailAuthTypeOptions,
    (CredentialTypes.GIT, "auth_type"): GitAuthTypeOptions,
    (CredentialTypes.MS_EXCHANGE, "auth_type"): ExchangeAuthTypeOptions,
    (CredentialTypes.SCHEDULER, "resource_type"): SchedulerResourceTypeOptions,
    (CredentialTypes.SHAREPOINT, "auth_type"): SharePointAuthTypeOptions,
    (CredentialTypes.SQL, "dialect"): SqlDialectOptions,
    (CredentialTypes.WEBHOOK, "gitlab_event_filter"): WebhookGitlabEventFilterOptions,
    (CredentialTypes.WEBHOOK, "resource_type"): WebhookResourceTypeOptions,
}
