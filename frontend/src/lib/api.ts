import { buildApiUrl } from "./config";
import { getStoredAccessToken } from "./storage";

type RequestOptions = {
  method?: string;
  body?: BodyInit | object;
  headers?: HeadersInit;
};

type ErrorPayload = {
  detail?: string;
  message?: string;
  code?: string;
  [key: string]: unknown;
};

function buildApiErrorMessage({
  statusCode,
  errorPayload,
}: {
  statusCode: number;
  errorPayload: ErrorPayload | null;
}): string {
  const baseMessage =
    errorPayload?.detail ||
    errorPayload?.message ||
    "Request failed. Please try again.";

  const codeSuffix = errorPayload?.code ? ` [${errorPayload.code}]` : "";
  return `${baseMessage} (HTTP ${statusCode})${codeSuffix}`;
}

export class ApiError extends Error {
  statusCode: number;
  requestPath: string;
  requestMethod: string;
  errorPayload: ErrorPayload | string | null;

  constructor(
    message: string,
    statusCode: number,
    requestPath = "",
    requestMethod = "GET",
    errorPayload: ErrorPayload | string | null = null,
  ) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.requestPath = requestPath;
    this.requestMethod = requestMethod;
    this.errorPayload = errorPayload;
  }
}

export async function apiRequest<T>(
  path: string,
  { method = "GET", body, headers }: RequestOptions = {},
): Promise<T> {
  const accessToken = getStoredAccessToken();
  const requestHeaders = new Headers(headers);
  const isFormDataBody = body instanceof FormData;
  const isStringBody = typeof body === "string";

  if (body !== undefined && !isFormDataBody && !isStringBody) {
    requestHeaders.set("Content-Type", "application/json");
  }

  if (accessToken) {
    requestHeaders.set("Authorization", `Bearer ${accessToken}`);
  }

  let response: Response;

  try {
    response = await fetch(buildApiUrl(path), {
      method,
      headers: requestHeaders,
      body:
        body === undefined
          ? undefined
          : isFormDataBody
            ? body
            : isStringBody
              ? body
              : JSON.stringify(body),
    });
  } catch (error) {
    throw new ApiError(
      error instanceof Error
        ? `Network error. ${error.message}`
        : "Network error. Please check your connection and backend server.",
      0,
      path,
      method,
      error instanceof Error ? error.message : null,
    );
  }

  if (!response.ok) {
    const errorPayload = (await tryReadJson(response)) as ErrorPayload | null;
    const message = buildApiErrorMessage({
      statusCode: response.status,
      errorPayload,
    });

    throw new ApiError(message, response.status, path, method, errorPayload);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type")?.toLowerCase() || "";
  const responseText = await response.text();

  if (!responseText.trim()) {
    return undefined as T;
  }

  if (!contentType.includes("application/json")) {
    return responseText as T;
  }

  try {
    return JSON.parse(responseText) as T;
  } catch {
    throw new ApiError(
      "Server returned an unexpected response format.",
      response.status,
      path,
      method,
      responseText,
    );
  }
}

async function tryReadJson(response: Response): Promise<unknown | null> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}
