/**
 * Token storage. Kept isolated in this one file so if we ever want to switch
 * storage strategy (e.g. httpOnly cookies via a Next.js route handler) there's
 * exactly one place to change.
 */
const ACCESS_KEY = 'mpm_access_token';
const REFRESH_KEY = 'mpm_refresh_token';

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function setAccessToken(access: string) {
  localStorage.setItem(ACCESS_KEY, access);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}
