import { appConfig } from "./config";

let cachedBrowserStorage: Storage | null | undefined;
let didLogStorageAccessFailure = false;

function getBrowserStorage(): Storage | null {
  if (cachedBrowserStorage !== undefined) {
    return cachedBrowserStorage;
  }

  if (typeof window === "undefined" || !("localStorage" in window)) {
    cachedBrowserStorage = null;
    return cachedBrowserStorage;
  }

  try {
    cachedBrowserStorage = window.localStorage;
    return cachedBrowserStorage;
  } catch (error) {
    if (!didLogStorageAccessFailure) {
      console.error("Failed to access browser localStorage", error);
      didLogStorageAccessFailure = true;
    }
    cachedBrowserStorage = null;
    return cachedBrowserStorage;
  }
}

export function getStoredAccessToken(): string | null {
  return getBrowserStorage()?.getItem(appConfig.accessTokenStorageKey) ?? null;
}

export function storeAccessToken(accessToken: string): void {
  getBrowserStorage()?.setItem(appConfig.accessTokenStorageKey, accessToken);
}

export function clearStoredAccessToken(): void {
  getBrowserStorage()?.removeItem(appConfig.accessTokenStorageKey);
}
