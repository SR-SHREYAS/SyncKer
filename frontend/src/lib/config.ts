const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_ACCESS_TOKEN_STORAGE_KEY = "syncker.access_token";

function normalizeApiBaseUrl(value: string): string {
  return value.replace(/\/+$/, "");
}

export const appConfig = {
  apiBaseUrl: normalizeApiBaseUrl(
    import.meta.env.VITE_API_BASE_URL?.trim() || DEFAULT_API_BASE_URL,
  ),
  accessTokenStorageKey:
    import.meta.env.VITE_ACCESS_TOKEN_STORAGE_KEY?.trim() ||
    DEFAULT_ACCESS_TOKEN_STORAGE_KEY,
};

export function buildApiUrl(path: string): string {
  const normalizedPath = path.replace(/^\/+/, "");
  return `${appConfig.apiBaseUrl}/${normalizedPath}`;
}
