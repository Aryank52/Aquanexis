import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { authApi } from '@/api/endpoints';
import {
  setTokens,
  clearTokens,
  getAccessToken,
  hasValidSession,
  setSessionExpiredHandler,
} from '@/api/client';
import type { AuthUser, LoginRequest, LoginResponse } from '@/types/api';

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    if (!hasValidSession()) {
      setIsLoading(false);
      return;
    }

    try {
      // In a real app, you'd validate the token with the backend
      // For now, we'll just check if we have a token
      const token = getAccessToken();
      if (token) {
        // Try to get user info from token or storage
        // This is a simplified version - in production you'd call an API
        setIsLoading(false);
      } else {
        setIsLoading(false);
      }
    } catch {
      clearTokens();
      setUser(null);
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();

    // Set up session expired handler
    setSessionExpiredHandler(() => {
      clearTokens();
      setUser(null);
      window.location.href = '/login';
    });
  }, [checkAuth]);

  const login = async (credentials: LoginRequest) => {
    setIsLoading(true);
    try {
      const response = await authApi.login(credentials);
      setTokens(response.access_token, response.refresh_token);
      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore logout errors
    } finally {
      clearTokens();
      setUser(null);
      window.location.href = '/login';
    }
  };

  const refreshSession = async () => {
    // In a real app, you'd call the refresh token endpoint
    // For now, just re-check auth
    await checkAuth();
  };

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated: !!user, isLoading, login, logout, refreshSession }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
