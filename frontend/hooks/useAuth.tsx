'use client';

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/endpoints';
import { clearTokens, getAccessToken, setTokens } from '@/lib/auth';
import { getRefreshToken } from '@/lib/auth';
import type { User } from '@/types';
import { getErrorMessage } from '@/lib/utils';

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (data: { username: string; email: string; password: string; password_confirm: string }) => Promise<void>;
  logout: () => Promise<void>;
  refetchUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  async function refetchUser() {
    if (!getAccessToken()) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const me = await authApi.me();
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    // queueMicrotask defers the call so no branch of refetchUser can call
    // setState synchronously within the effect's own call stack (React's
    // set-state-in-effect rule flags that even when the state is correct).
    queueMicrotask(() => {
      refetchUser();
    });
  }, []);

  async function login(username: string, password: string) {
    const data = await authApi.login({ username, password });
    setTokens(data.access, data.refresh);
    setUser(data.user);
  }

  async function register(payload: { username: string; email: string; password: string; password_confirm: string }) {
  await authApi.register(payload);
  clearTokens();
  setUser(null);
}

  async function logout() {
    const refresh = getRefreshToken();
    try {
      if (refresh) await authApi.logout(refresh);
    } catch (err) {
      // Even if the blacklist call fails (e.g. token already expired), we still
      // want to clear local state so the user isn't stuck "logged in" client-side.
      console.warn('Logout request failed:', getErrorMessage(err));
    }
    clearTokens();
    setUser(null);
    router.push('/login');
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout, refetchUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
