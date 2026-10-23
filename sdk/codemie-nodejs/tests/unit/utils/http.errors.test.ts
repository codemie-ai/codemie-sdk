import axios, { type AxiosError } from "axios";
import { beforeEach, describe, expect, it, jest } from "@jest/globals";
import { ApiError, NotFoundError } from "../../../src/exceptions";
import { ApiRequestHandler } from "../../../src/utils/http";

jest.mock("axios", () => ({ create: jest.fn() }));

describe("HTTP error diagnostics", () => {
  let rejectResponse: (error: AxiosError) => never;

  beforeEach(() => {
    const responseUse = jest.fn();
    (axios.create as jest.Mock).mockReturnValue({
      interceptors: { response: { use: responseUse }, request: { use: jest.fn() } },
    });
    new ApiRequestHandler({ apiDomain: "https://api.example.com" });
    rejectResponse = responseUse.mock.calls[0][1] as (error: AxiosError) => never;
  });

  function failure(status: number, data: unknown): AxiosError {
    return {
      message: `Request failed with status ${status}`,
      code: "ERR_BAD_REQUEST",
      config: {
        method: "post",
        url: "https://user:password@api.example.com/v1/assistants?token=secret#private",
        headers: { Authorization: "Bearer secret", Cookie: "private" },
        data: { password: "private" },
      },
      response: { status, data, headers: { "x-request-id": "request-123" } },
    } as unknown as AxiosError;
  }

  it.each([404, 400, 401, 403, 422, 500])("preserves status %i and the original body", (status) => {
    const body = { error: { message: "Rejected", details: "Useful server detail" } };
    try {
      rejectResponse(failure(status, body));
    } catch (error) {
      expect(error).toBeInstanceOf(status === 404 ? NotFoundError : ApiError);
      expect(error).toMatchObject({ statusCode: status, response: body });
      expect((error as Error).message).toContain("Useful server detail");
      expect((error as ApiError).response).toBe(body);
      return;
    }
    throw new Error("Expected an API error");
  });

  it.each(["plain response", ["validation detail"], null])("retains a non-object body: %p", (body) => {
    expect(() => rejectResponse(failure(404, body))).toThrow(ApiError);
    try {
      rejectResponse(failure(404, body));
    } catch (error) {
      expect((error as ApiError).response).toBe(body);
    }
  });

  it("keeps useful request context without credentials, body, query or fragment", () => {
    try {
      rejectResponse(failure(404, { error: { message: "Not found" } }));
    } catch (error) {
      expect((error as ApiError).request).toEqual({
        method: "POST",
        path: "/v1/assistants",
        requestId: "request-123",
        code: "ERR_BAD_REQUEST",
      });
      expect(JSON.stringify((error as ApiError).request)).not.toMatch(/secret|password|private/);
    }
  });

  it("does not invent HTTP 500 for a network error or mask a malformed URL", () => {
    const error = {
      message: "Connection reset",
      code: "ECONNRESET",
      config: { url: "http://[", method: "get" },
    } as AxiosError;
    try {
      rejectResponse(error);
    } catch (caught) {
      expect(caught).toMatchObject({ message: "Connection reset", request: { code: "ECONNRESET" } });
      expect((caught as ApiError).statusCode).toBeUndefined();
      expect((caught as ApiError).request?.path).toBeUndefined();
    }
  });
});
