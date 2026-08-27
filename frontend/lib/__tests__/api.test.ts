import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ApiRequestError, api, buildQuery } from '../api';
import { clearTokens, setTokens, getAccessToken } from '../auth';

describe('buildQuery', () => {
  it('omits undefined, null, and empty-string values', () => {
    expect(buildQuery({ search: 'dune', genre: undefined, year: null as unknown as undefined, page: '' })).toBe(
      '?search=dune'
    );
  });

  it('returns an empty string when nothing is set', () => {
    expect(buildQuery({})).toBe('');
  });

  it('serializes multiple params', () => {
    const qs = buildQuery({ search: 'a', page: 2 });
    expect(qs).toContain('search=a');
    expect(qs).toContain('page=2');
  });
});

describe('ApiRequestError', () => {
  it('prefers a top-level detail message', () => {
    const err = new ApiRequestError(400, { detail: 'Invalid credentials.' });
    expect(err.message).toBe('Invalid credentials.');
    expect(err.status).toBe(400);
  });

  it('falls back to the first field validation error (DRF style)', () => {
    const err = new ApiRequestError(400, { username: ['A user with that username already exists.'] });
    expect(err.message).toBe('A user with that username already exists.');
  });

  it('falls back to a generic message when the body is empty', () => {
    const err = new ApiRequestError(500, {});
    expect(err.message).toBe('Something went wrong.');
  });
});

describe('api client', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    clearTokens();
    localStorage.clear();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it('attaches the Bearer token from storage to authenticated requests', async () => {
    setTokens('access-123', 'refresh-456');
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      })
    );
    global.fetch = fetchMock as unknown as typeof fetch;

    await api.get('/movies/');

    const [, init] = fetchMock.mock.calls[0];
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer access-123');
  });

  it('does not attach a token for skipAuth requests even when one is stored', async () => {
    setTokens('access-123', 'refresh-456');
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      })
    );
    global.fetch = fetchMock as unknown as typeof fetch;

    await api.post('/auth/login/', { username: 'x', password: 'y' }, { skipAuth: true });

    const [, init] = fetchMock.mock.calls[0];
    expect((init.headers as Record<string, string>).Authorization).toBeUndefined();
  });

  it('throws ApiRequestError with the response body on a non-2xx response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Not found.' }), {
        status: 404,
        headers: { 'content-type': 'application/json' },
      })
    );
    global.fetch = fetchMock as unknown as typeof fetch;

    await expect(api.get('/movies/9999/')).rejects.toMatchObject({ status: 404, message: 'Not found.' });
  });

  it('returns undefined for a 204 No Content response instead of parsing a body', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    global.fetch = fetchMock as unknown as typeof fetch;

    const result = await api.delete('/favorites/1/');
    expect(result).toBeUndefined();
  });

  it('transparently refreshes an expired access token and retries the original request once', async () => {
    setTokens('expired-token', 'refresh-456');

    const fetchMock = vi
      .fn()
      // First call: the original request comes back 401 (expired).
      .mockResolvedValueOnce(new Response(null, { status: 401 }))
      // Second call: the refresh endpoint succeeds with a new access token.
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ access: 'fresh-token' }), {
          status: 200,
          headers: { 'content-type': 'application/json' },
        })
      )
      // Third call: the retried original request succeeds.
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: 1 }), {
          status: 200,
          headers: { 'content-type': 'application/json' },
        })
      );
    global.fetch = fetchMock as unknown as typeof fetch;

    const result = await api.get('/auth/me/');

    expect(result).toEqual({ id: 1 });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(getAccessToken()).toBe('fresh-token');
    // The retried request should carry the newly refreshed token.
    const retryCall = fetchMock.mock.calls[2];
    expect((retryCall[1].headers as Record<string, string>).Authorization).toBe('Bearer fresh-token');
  });
});
