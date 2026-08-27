import { clearTokens, getAccessToken, getRefreshToken, setAccessToken } from './auth';
import type { ApiError } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export class ApiRequestError extends Error {
  status: number;
  body: ApiError;

  constructor(status: number, body: ApiError) {
    // Prefer a top-level "detail" message; otherwise take the first field error we find,
    // which is how DRF reports validation errors (e.g. {"username": ["already exists"]}).
    const firstFieldError = Object.values(body || {})[0];
    const message =
      body?.detail ||
      (Array.isArray(firstFieldError) ? firstFieldError[0] : (firstFieldError as string)) ||
      'Something went wrong.';
    super(String(message));
    this.status = status;
    this.body = body;
  }
}

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  // Multiple 401s can land at once; de-dupe into a single in-flight refresh call.
  if (!refreshPromise) {
    refreshPromise = fetch(`${API_URL}/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })
      .then(async (res) => {
        if (!res.ok) return null;
        const data = await res.json();
        setAccessToken(data.access);
        return data.access as string;
      })
      .catch(() => null)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  skipAuth?: boolean;
  isRetry?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, skipAuth, isRetry, headers, ...rest } = options;

  const finalHeaders: Record<string, string> = {
    Accept: 'application/json',
    ...(headers as Record<string, string>),
  };

  let finalBody: BodyInit | undefined;
  if (body !== undefined) {
    finalHeaders['Content-Type'] = 'application/json';
    finalBody = JSON.stringify(body);
  }

  if (!skipAuth) {
    const token = getAccessToken();
    if (token) finalHeaders['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...rest,
    headers: finalHeaders,
    body: finalBody,
  });

  // Access token expired mid-session — refresh once and retry the original request.
  if (res.status === 401 && !skipAuth && !isRetry) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      return request<T>(path, { ...options, isRetry: true });
    }
    clearTokens();
    if (typeof window !== 'undefined') {
      // Intentionally a hard navigation (not router.push): this runs from a
      // plain fetch wrapper with no access to Next's router, and a full
      // reload guarantees no stale authenticated state lingers in memory.
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.href = '/login';
    }
    throw new ApiRequestError(401, { detail: 'Session expired. Please log in again.' });
  }

  if (res.status === 204) {
    return undefined as T;
  }

  const contentType = res.headers.get('content-type') || '';
  const data = contentType.includes('application/json') ? await res.json() : null;

  if (!res.ok) {
    throw new ApiRequestError(res.status, data || {});
  }

  return data as T;
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) => request<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'POST', body }),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'PATCH', body }),
  delete: <T>(path: string, options?: RequestOptions) => request<T>(path, { ...options, method: 'DELETE' }),
};

export function buildQuery(params: Record<string, string | number | boolean | undefined | null>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value));
    }
  });
  const qs = search.toString();
  return qs ? `?${qs}` : '';
}
