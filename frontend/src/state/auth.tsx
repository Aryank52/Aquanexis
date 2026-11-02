import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '@/api/endpoints';
import {
  setTokens,
  clearTokens,
  hasValidSession,
  setSessionExpiredHandler,
} from '@/api/client';
import type { AuthUser } from '@/types/api';

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = user !== null;

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Best-effort server logout; clear local state regardless
    } finally {
      clearTokens();
      setUser(null);
      navigate('/login', { replace: true });
    }
  }, [navigate]);

  // Register session-expired handler so the client interceptor
  // can redirect when a refresh token fails.
  useEffect(() => {
    setSessionExpiredHandler(() => {
      clearTokens();
      setUser(null);
      navigate('/session-expired', { replace: true });
    });
  }, [navigate]);

  // On mount, check whether we still hold a valid in-memory session.
  // Tokens are in-memory only, so a page reload always starts logged out.
  useEffect(() => {
    if (hasValidSession()) {
      // Tokens survive only within the same SPA session (no page reload).
      // If we still have an access token the user was previously authenticated.
      // We cannot recover the user object without an API call, so treat as
      // logged out on hard refresh (tokens cleared).
      setIsLoading(false);
    } else {
      clearTokens();
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(
    async (username: string, password: string) => {
      const response = await authApi.login({ username, password });
      setTokens(response.access_token, response.refresh_token);
      setUser(response.user);
    },
    []
  );

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated, isLoading, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
