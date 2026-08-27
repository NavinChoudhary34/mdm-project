import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuth } from '../useAuth';
import { getAccessToken, getRefreshToken } from '../../lib/auth';

// next/navigation's useRouter needs a mock outside the App Router context.
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

const mockUser = { id: 1, username: 'navin', email: 'navin@example.com', bio: '', avatar_url: '', date_joined: '' };

function TestConsumer() {
  const { user, isLoading, login, logout } = useAuth();
  return (
    <div>
      <span data-testid="status">{isLoading ? 'loading' : user ? `logged-in:${user.username}` : 'logged-out'}</span>
      <button onClick={() => login('navin', 'pw')}>Log in</button>
      <button onClick={() => logout()}>Log out</button>
    </div>
  );
}

describe('useAuth', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('starts logged out when there is no stored token', async () => {
    global.fetch = vi.fn() as unknown as typeof fetch;
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('logged-out'));
  });

  it('login stores tokens and updates the user in context', async () => {
    global.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ user: mockUser, access: 'access-tok', refresh: 'refresh-tok' }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      })
    ) as unknown as typeof fetch;

    const user = userEvent.setup();
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('logged-out'));
    await user.click(screen.getByText('Log in'));

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('logged-in:navin'));
    expect(getAccessToken()).toBe('access-tok');
    expect(getRefreshToken()).toBe('refresh-tok');
  });

  it('logout clears tokens and resets the user even if the blacklist call fails', async () => {
    global.fetch = vi
      .fn()
      // login
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ user: mockUser, access: 'access-tok', refresh: 'refresh-tok' }), {
          status: 200,
          headers: { 'content-type': 'application/json' },
        })
      )
      // logout request fails server-side (e.g. token already expired)
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'Invalid token.' }), { status: 400 })) as unknown as typeof fetch;

    const user = userEvent.setup();
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('logged-out'));
    await user.click(screen.getByText('Log in'));
    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('logged-in:navin'));

    await user.click(screen.getByText('Log out'));

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('logged-out'));
    // Local session state must be cleared client-side regardless of whether
    // the server-side blacklist call succeeded.
    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });
});
