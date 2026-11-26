import { ApiRequestHandler, formatCookies } from "../../../src/utils/http";
import { describe, expect, it, jest, beforeEach } from "@jest/globals";

jest.mock("axios", () => ({
  create: jest.fn().mockReturnValue({
    interceptors: {
      response: {
        use: jest.fn(),
      },
      request: {
        use: jest.fn(),
      },
    },
    request: jest.fn(),
    post: jest.fn(),
  }),
}));
import axios from "axios";
import { ProjectService } from "../../../src/services/project";

describe("ApiRequestHandler", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("constructor", () => {
    it("should create an instance with the correct base URL and headers", () => {
      const apiRequestHandler = new ApiRequestHandler({
        apiDomain: "domain",
        token: "token",
        verifySSL: false,
      });
      expect(apiRequestHandler).toBeDefined();
      expect(axios.create).toHaveBeenCalledWith({
        baseURL: "domain",
        validateStatus: expect.any(Function),
        headers: {
          Authorization: "Bearer token",
          "Content-Type": "application/json",
        },
        httpsAgent: expect.any(Object),
      });
    });
  });

  describe("constructor with cookies", () => {
    it("should create an instance with Cookie header when cookies are provided", () => {
      const cookies = { JSESSIONID: "abc123", "XSRF-TOKEN": "xyz789" };
      new ApiRequestHandler({ apiDomain: "domain", token: null, verifySSL: false, cookies });

      expect(axios.create).toHaveBeenCalledWith({
        baseURL: "domain",
        validateStatus: expect.any(Function),
        headers: {
          Cookie: "JSESSIONID=abc123; XSRF-TOKEN=xyz789",
          "Content-Type": "application/json",
        },
        httpsAgent: expect.any(Object),
      });
    });

    it("should create an instance with Authorization header when token is provided", () => {
      new ApiRequestHandler({ apiDomain: "domain", token: "token", verifySSL: false });

      expect(axios.create).toHaveBeenCalledWith({
        baseURL: "domain",
        validateStatus: expect.any(Function),
        headers: {
          Authorization: "Bearer token",
          "Content-Type": "application/json",
        },
        httpsAgent: expect.any(Object),
      });
    });

    it("should prefer cookies over token when both are provided", () => {
      const cookies = { SESSION: "cookie-value" };
      new ApiRequestHandler({ apiDomain: "domain", token: "token", verifySSL: false, cookies });

      expect(axios.create).toHaveBeenCalledWith({
        baseURL: "domain",
        validateStatus: expect.any(Function),
        headers: {
          Cookie: "SESSION=cookie-value",
          "Content-Type": "application/json",
        },
        httpsAgent: expect.any(Object),
      });
    });

    it("should create an instance with only Content-Type header when no auth provided", () => {
      new ApiRequestHandler({ apiDomain: "domain", token: null, verifySSL: false });

      expect(axios.create).toHaveBeenCalledWith({
        baseURL: "domain",
        validateStatus: expect.any(Function),
        headers: {
          "Content-Type": "application/json",
        },
        httpsAgent: expect.any(Object),
      });
    });
  });

  describe("formatCookies", () => {
    it("should format single cookie correctly", () => {
      const cookies = { JSESSIONID: "abc123" };
      const result = formatCookies(cookies);
      expect(result).toBe("JSESSIONID=abc123");
    });

    it("should format multiple cookies correctly", () => {
      const cookies = { JSESSIONID: "abc123", "XSRF-TOKEN": "xyz789", SESSION: "test" };
      const result = formatCookies(cookies);
      expect(result).toBe("JSESSIONID=abc123; XSRF-TOKEN=xyz789; SESSION=test");
    });

    it("should return empty string for empty cookies object", () => {
      const cookies = {};
      const result = formatCookies(cookies);
      expect(result).toBe("");
    });
  });

  describe("HTTP methods", () => {
    let apiRequestHandler: ApiRequestHandler;
    const mockResponse = { data: { data: { result: "success" } } };

    beforeEach(() => {
      // Mock axios request and post methods
      const mockClient = {
        interceptors: {
          response: {
            use: jest.fn(),
          },
        },
        request: jest.fn().mockResolvedValue(mockResponse as never),
        post: jest.fn().mockResolvedValue(mockResponse as never),
      };

      // Configure the mock implementation
      (axios.create as jest.Mock).mockReturnValue(mockClient);

      // Create instance after setting up mocks
      apiRequestHandler = new ApiRequestHandler({
        apiDomain: "domain",
        token: "token",
        verifySSL: false,
      });
    });

    it("should make a GET request with correct parameters", async () => {
      const axiosInstance = axios.create();

      await apiRequestHandler.get("/test-path", { param: "value" });

      expect(axiosInstance.request).toHaveBeenCalledWith({
        method: "get",
        url: "/test-path",
        params: { param: "value" },
      });
    });

    it("should make a POST request with correct parameters", async () => {
      const axiosInstance = axios.create();
      const postData = { key: "value" };

      await apiRequestHandler.post("/test-path", postData);

      expect(axiosInstance.request).toHaveBeenCalledWith({
        method: "post",
        url: "/test-path",
        data: postData,
      });
    });

    it("should make a PUT request with correct parameters", async () => {
      const axiosInstance = axios.create();
      const putData = { key: "updated" };

      await apiRequestHandler.put("/test-path", putData);

      expect(axiosInstance.request).toHaveBeenCalledWith({
        method: "put",
        url: "/test-path",
        data: putData,
      });
    });

    it("should make a PATCH request and return response data", async () => {
      const axiosInstance = axios.create();
      const patchData = { key: "patched" };

      const result = await apiRequestHandler.patch("/test-path", patchData);

      expect(axiosInstance.request).toHaveBeenCalledWith({
        method: "patch",
        url: "/test-path",
        data: patchData,
      });
      expect(result).toEqual(mockResponse.data);
    });

    it("should pass params and paramsSerializer through on DELETE", async () => {
      const axiosInstance = axios.create();
      const paramsSerializer = (p: Record<string, string[]>) =>
        p.user_id.map((v) => `user_id=${v}`).join("&");
      const params = { user_id: ["a", "b"] };

      await apiRequestHandler.delete("/test-path", { params, paramsSerializer });

      const call = (axiosInstance.request as jest.Mock).mock.calls[0][0] as {
        params: Record<string, string[]>;
        paramsSerializer: (p: Record<string, string[]>) => string;
      };
      expect(call.paramsSerializer(call.params)).toBe("user_id=a&user_id=b");
    });

    it("should make a DELETE request with correct parameters", async () => {
      const axiosInstance = axios.create();

      await apiRequestHandler.delete("/test-path");

      expect(axiosInstance.request).toHaveBeenCalledWith({
        method: "delete",
        url: "/test-path",
      });
    });

    it("should handle stream requests correctly", async () => {
      const axiosInstance = axios.create();
      const streamData = { stream: true };

      await apiRequestHandler.stream("/stream-path", streamData);

      expect(axiosInstance.post).toHaveBeenCalledWith(
        "/stream-path",
        streamData,
        expect.any(Object),
      );
    });
  });

  describe("projectExists with real 404 mapping", () => {
    it("resolves false when axios rejects with a 404", async () => {
      let onError: (e: unknown) => unknown = () => undefined;
      const client = {
        interceptors: {
          response: { use: jest.fn((_ok: unknown, err: (e: unknown) => unknown) => (onError = err)) },
          request: { use: jest.fn() },
        },
        request: jest.fn(async () => onError({ response: { status: 404, data: {} } })),
      };
      (axios.create as jest.Mock).mockReturnValue(client);

      const service = new ProjectService({ apiDomain: "domain", token: "t" });

      await expect(service.projectExists("missing")).resolves.toBe(false);
    });
  });

  describe("constructor with tokenGetter", () => {
    let requestInterceptorUseMock: jest.Mock;

    beforeEach(() => {
      requestInterceptorUseMock = jest.fn();
      (axios.create as jest.Mock).mockReturnValue({
        interceptors: {
          response: { use: jest.fn() },
          request: { use: requestInterceptorUseMock },
        },
        request: jest.fn(),
        post: jest.fn(),
      });
    });

    it("should register a request interceptor when tokenGetter is provided", () => {
      const tokenGetter = jest.fn<() => Promise<string>>().mockResolvedValue("dynamic-token");

      new ApiRequestHandler({ apiDomain: "domain", token: null, verifySSL: false, tokenGetter });

      expect(requestInterceptorUseMock).toHaveBeenCalledTimes(1);
    });

    it("should not register a request interceptor when tokenGetter is null", () => {
      new ApiRequestHandler({ apiDomain: "domain", token: "static", verifySSL: false, tokenGetter: null });

      expect(requestInterceptorUseMock).not.toHaveBeenCalled();
    });

    it("should not register a request interceptor when tokenGetter is omitted", () => {
      new ApiRequestHandler({ apiDomain: "domain", token: "static", verifySSL: false });

      expect(requestInterceptorUseMock).not.toHaveBeenCalled();
    });
  });
});
