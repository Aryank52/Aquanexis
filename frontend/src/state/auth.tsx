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
import type { AuthUser, LoginRequest } from '@/types/api';

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const USER_STORAGE_KEY = 'aquanexis_auth_user';
const LOGGED_OUT_KEY = 'aquanexis_explicit_logout';

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [user, setUser] = useState<AuthUser | null>(() => {
    if (typeof window !== 'undefined') {
      const saved = sessionStorage.getItem(USER_STORAGE_KEY);
      if (saved && hasValidSession()) {
        try {
          return JSON.parse(saved) as AuthUser;
        } catch {
          return null;
        }
      }
    }
    return null;
  });
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = user !== null;

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Best-effort server logout; clear local state regardless
    } finally {
      clearTokens();
      if (typeof window !== 'undefined') {
        sessionStorage.removeItem(USER_STORAGE_KEY);
        sessionStorage.setItem(LOGGED_OUT_KEY, 'true');
      }
      setUser(null);
      navigate('/login', { replace: true });
    }
  }, [navigate]);

  // Register session-expired handler so the client interceptor
  // can redirect when a refresh token fails.
  useEffect(() => {
    setSessionExpiredHandler(() => {
      clearTokens();
      if (typeof window !== 'undefined') {
        sessionStorage.removeItem(USER_STORAGE_KEY);
      }
      setUser(null);
      navigate('/session-expired', { replace: true });
    });
  }, [navigate]);

  // On mount, restore session from sessionStorage or auto-authenticate in demo mode
  useEffect(() => {
    let active = true;
    async function initAuth() {
      if (hasValidSession() && user) {
        if (active) setIsLoading(false);
        return;
      }
      const explicitLogout = typeof window !== 'undefined' && sessionStorage.getItem(LOGGED_OUT_KEY) === 'true';
      if (!explicitLogout) {
        try {
          const response = await authApi.login({ username: 'admin', password: 'password123' });
          if (active) {
            setTokens(response.access_token, response.refresh_token);
            if (typeof window !== 'undefined') {
              sessionStorage.setItem(USER_STORAGE_KEY, JSON.stringify(response.user));
            }
            setUser(response.user);
            setIsLoading(false);
            return;
          }
        } catch {
          // Fall through to unauthenticated state if backend is offline or rejects demo login
        }
      }
      clearTokens();
      if (active) setIsLoading(false);
    }
    initAuth();
    return () => {
      active = false;
    };
  }, [user]);

  const login = useCallback(
    async (credentials: LoginRequest) => {
      const response = await authApi.login(credentials);
      setTokens(response.access_token, response.refresh_token);
      if (typeof window !== 'undefined') {
        sessionStorage.removeItem(LOGGED_OUT_KEY);
        sessionStorage.setItem(USER_STORAGE_KEY, JSON.stringify(response.user));
      }
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