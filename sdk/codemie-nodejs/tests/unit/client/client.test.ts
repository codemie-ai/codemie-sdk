import { beforeEach, describe, expect, it, jest } from "@jest/globals";
import { KeycloakCredentials } from "../../../src/auth/credentials";
import { CodeMieClient, type CodeMieClientConfig } from "../../../src/client/client";
import { ProjectService } from "../../../src/services/project";

jest.mock("axios", () => ({
  create: jest.fn().mockImplementation(() => ({
    interceptors: {
      response: { use: jest.fn() },
      request: { use: jest.fn() },
    },
  })),
  post: jest.fn(),
  get: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
}));
jest.mock("../../../src/auth/credentials");
jest.mock("../../../src/services/project");

describe("CodeMieClient", () => {
  const mockConfig: CodeMieClientConfig = {
    auth_server_url: "https://auth.example.com",
    auth_realm_name: "test-realm",
    codemie_api_domain: "https://api.example.com",
    auth_client_id: "test-client",
    auth_client_secret: "test-secret",
    username: "test-user",
    password: "test-password",
    verify_ssl: true,
  };

  const keycloakCredentialsMock = {
    getToken: jest.fn<() => string>(),
    clearCache: jest.fn(),
  };

  let client: CodeMieClient;

  beforeEach(() => {
    jest.clearAllMocks();
    (KeycloakCredentials as unknown as jest.Mock).mockImplementation(() => keycloakCredentialsMock);
    client = new CodeMieClient(mockConfig);
  });

  describe("constructor", () => {
    it("should create an instance with the provided configuration", () => {
      expect(client).toBeInstanceOf(CodeMieClient);
      expect(KeycloakCredentials).toHaveBeenCalledWith({
        serverUrl: mockConfig.auth_server_url,
        realmName: mockConfig.auth_realm_name,
        clientId: mockConfig.auth_client_id,
        clientSecret: mockConfig.auth_client_secret,
        username: mockConfig.username,
        password: mockConfig.password,
        externalToken: undefined,
        externalIdp: undefined,
        verifySSL: mockConfig.verify_ssl,
      });
    });

    it("should set default verify_ssl to true if not provided", () => {
      const configWithoutSSL = { ...mockConfig };
      delete configWithoutSSL.verify_ssl;

      const clientWithoutSSL = new CodeMieClient(configWithoutSSL);

      expect(clientWithoutSSL).toBeInstanceOf(CodeMieClient);
      expect(KeycloakCredentials).toHaveBeenCalledWith({
        serverUrl: mockConfig.auth_server_url,
        realmName: mockConfig.auth_realm_name,
        clientId: mockConfig.auth_client_id,
        clientSecret: mockConfig.auth_client_secret,
        username: mockConfig.username,
        password: mockConfig.password,
        externalToken: undefined,
        externalIdp: undefined,
        verifySSL: true,
      });
    });

    it("should remove trailing slash from API domain", () => {
      const clientWithTrailingSlash = new CodeMieClient({
        ...mockConfig,
        codemie_api_domain: "https://api.example.com/",
      });

      expect(clientWithTrailingSlash).toBeInstanceOf(CodeMieClient);
    });

    it("should pass external_token and external_idp to KeycloakCredentials", () => {
      const externalTokenConfig: CodeMieClientConfig = {
        ...mockConfig,
        external_token: "ext-token-value",
        external_idp: "ext-idp-alias",
      };

      const externalTokenClient = new CodeMieClient(externalTokenConfig);

      expect(externalTokenClient).toBeInstanceOf(CodeMieClient);
      expect(KeycloakCredentials).toHaveBeenCalledWith(
        expect.objectContaining({
          externalToken: "ext-token-value",
          externalIdp: "ext-idp-alias",
        }),
      );
    });
  });

  describe("initialize", () => {
    it("should get token and refresh services", async () => {
      keycloakCredentialsMock.getToken.mockResolvedValueOnce("mock-token" as never);

      await client.initialize();

      expect(keycloakCredentialsMock.getToken).toHaveBeenCalled();
    });
  });

  describe("getToken", () => {
    it("should return existing token if available", async () => {
      keycloakCredentialsMock.getToken.mockResolvedValueOnce("mock-token" as never);

      await client.initialize();
      const token = await client.getToken();

      expect(token).toBe("mock-token");
    });
  });

  describe("cookie-based authentication", () => {
    const cookieConfig: CodeMieClientConfig = {
      codemie_api_domain: "https://api.example.com",
      cookies: {
        JSESSIONID: "abc123",
        "XSRF-TOKEN": "xyz789",
      },
      verify_ssl: false,
    };

    let cookieClient: CodeMieClient;

    beforeEach(() => {
      jest.clearAllMocks();
      cookieClient = new CodeMieClient(cookieConfig);
    });

    it("should create client with cookies without initializing Keycloak auth", () => {
      expect(cookieClient).toBeInstanceOf(CodeMieClient);
      expect(cookieClient.assistants).toBeDefined();
      expect(cookieClient.llms).toBeDefined();
    });

    it("should make initialize() a no-op when using cookies", async () => {
      await cookieClient.initialize();
      // Should not throw and should complete immediately
      expect(keycloakCredentialsMock.getToken).not.toHaveBeenCalled();
    });

    it("should return null from getToken() when using cookies", async () => {
      const token = await cookieClient.getToken();
      expect(token).toBeNull();
      expect(keycloakCredentialsMock.getToken).not.toHaveBeenCalled();
    });

    it("should throw error when calling refreshToken() with cookie auth", async () => {
      await expect(cookieClient.refreshToken()).rejects.toThrow(
        "Token refresh is not supported with cookie-based authentication",
      );
    });

    it("should work without auth_server_url and auth_realm_name when using cookies", () => {
      const minimalCookieConfig: CodeMieClientConfig = {
        codemie_api_domain: "https://api.example.com",
        cookies: { SESSION: "test" },
      };

      const minimalClient = new CodeMieClient(minimalCookieConfig);
      expect(minimalClient).toBeInstanceOf(CodeMieClient);
    });
  });

  describe("projects", () => {
    it("should expose a ProjectService and rebuild it on refresh", async () => {
      keycloakCredentialsMock.getToken.mockResolvedValue("token" as never);
      expect(client.projects).toBeInstanceOf(ProjectService);
      const before = (ProjectService as unknown as jest.Mock).mock.calls.length;

      await client.refreshToken();

      expect((ProjectService as unknown as jest.Mock).mock.calls.length).toBeGreaterThan(before);
    });
  });

  describe("refreshToken", () => {
    it("should call clearCache() before fetching a new token on each refresh", async () => {
      keycloakCredentialsMock.getToken.mockResolvedValue("refreshed-token" as never);

      await client.initialize();
      await client.refreshToken();
      await client.refreshToken();

      expect(keycloakCredentialsMock.clearCache).toHaveBeenCalledTimes(2);
      // initialize() + 2x refreshToken() = 3 getToken calls total
      expect(keycloakCredentialsMock.getToken).toHaveBeenCalledTimes(3);
    });
  });

  describe("validation", () => {
    it("should throw error when auth_server_url is missing for token auth", () => {
      const invalidConfig = {
        codemie_api_domain: "https://api.example.com",
        auth_realm_name: "test-realm",
        username: "user",
        password: "pass",
      };

      expect(() => new CodeMieClient(invalidConfig as CodeMieClientConfig)).toThrow(
        "auth_server_url and auth_realm_name are required when not using cookie authentication",
      );
    });

    it("should throw error when auth_realm_name is missing for token auth", () => {
      const invalidConfig = {
        codemie_api_domain: "https://api.example.com",
        auth_server_url: "https://auth.example.com",
        username: "user",
        password: "pass",
      };

      expect(() => new CodeMieClient(invalidConfig as CodeMieClientConfig)).toThrow(
        "auth_server_url and auth_realm_name are required when not using cookie authentication",
      );
    });

    it("should throw error when both auth fields are missing for token auth", () => {
      const invalidConfig = {
        codemie_api_domain: "https://api.example.com",
        username: "user",
        password: "pass",
      };

      expect(() => new CodeMieClient(invalidConfig as CodeMieClientConfig)).toThrow(
        "auth_server_url and auth_realm_name are required when not using cookie authentication",
      );
    });
  });
});
