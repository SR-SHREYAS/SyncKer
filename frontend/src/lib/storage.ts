const ACCESS_TOKEN_KEY = "syncker.access_token";

function getBrowserStorage(): Storage | null {
  if (typeof window === "undefined" || !("localStorage" in window)) {
    return null;
  }

  try {
    return window.localStorage;
  } catch (error) {
    console.error("Failed to access browser localStorage", error);
    return null;
  }
}

export function getStoredAccessToken(): string | null {
  return getBrowserStorage()?.getItem(ACCESS_TOKEN_KEY) ?? null;
}

export function storeAccessToken(accessToken: string): void {
  getBrowserStorage()?.setItem(ACCESS_TOKEN_KEY, accessToken);
}

export function clearStoredAccessToken(): void {
  getBrowserStorage()?.removeItem(ACCESS_TOKEN_KEY);
}
