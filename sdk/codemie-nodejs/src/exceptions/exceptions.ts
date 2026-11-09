import type { AnyJson } from "../models/common";

/** Useful diagnostic context, excluding request headers, body and query values. */
export interface ApiErrorRequestContext {
  method?: string;
  path?: string;
  requestId?: string;
  code?: string;
}

export class CodeMieError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CodeMieError";
  }
}

export class ApiError extends CodeMieError {
  statusCode?: number;
  response?: AnyJson;
  /** Raw response body exactly as received; may be a string, array, null or object. */
  body?: unknown;
  request?: ApiErrorRequestContext;

  constructor(
    message: string,
    statusCode?: number,
    response?: AnyJson,
    request?: ApiErrorRequestContext,
    body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.response = response;
    this.body = body === undefined ? response : body;
    this.request = request;
  }
}

export class NotFoundError extends ApiError {
  constructor(
    resourceType: string,
    resourceId: string,
    details?: { message?: string; response?: AnyJson; body?: unknown; request?: ApiErrorRequestContext },
  ) {
    super(
      details?.message || `${resourceType} with ${resourceId} not found`,
      404,
      details?.response,
      details?.request,
      details?.body,
    );
    this.name = "NotFoundError";
  }
}
