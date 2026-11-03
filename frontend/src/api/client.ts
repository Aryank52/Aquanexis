// ============================================================================
// AquaNexis API Client — Axios instance with auth interceptors
// ============================================================================
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type { APIError } from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

/**
 * Session token store — backed by sessionStorage so page refreshes during
 * a browser session preserve authentication, cleared on tab close or logout.
 */
const ACCESS_KEY = 'aquanexis_access_token';
const REFRESH_KEY = 'aquanexis_refresh_token';

let accessToken: string | null = typeof window !== 'undefined' ? sessionStorage.getItem(ACCESS_KEY) : null;
let refreshToken: string | null = typeof window !== 'undefined' ? sessionStorage.getItem(REFRESH_KEY) : null;
let onSessionExpired: (() => void) | null = null;

export function setTokens(access: string, refresh: string) {
  accessToken = access;
  refreshToken = refresh;
  if (typeof window !== 'undefined') {
    sessionStorage.setItem(ACCESS_KEY, access);
    sessionStorage.setItem(REFRESH_KEY, refresh);
  }
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  if (typeof window !== 'undefined') {
    sessionStorage.removeItem(ACCESS_KEY);
    sessionStorage.removeItem(REFRESH_KEY);
  }
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function hasValidSession(): boolean {
  return accessToken !== null;
}

export function setSessionExpiredHandler(handler: () => void) {
  onSessionExpired = handler;
}

// Create axios instance
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15_000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor — attach token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Track whether we're already refreshing to avoid concurrent refresh calls
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function subscribeToRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

// Response interceptor — handle 401 with token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<APIError>) => {
    const originalRequest = error.config;
    if (!originalRequest) return Promise.reject(error);

    // If 401 and we have a refresh token, try to refresh
    if (error.response?.status === 401 && refreshToken) {
      if (isRefreshing) {
        // Wait for the ongoing refresh
        return new Promise((resolve) => {
          subscribeToRefresh((newToken) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
            }
            resolve(apiClient(originalRequest));
          });
        });
      }

      isRefreshing = true;

      try {
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const newAccessToken = response.data.access_token;
        accessToken = newAccessToken;
        isRefreshing = false;
        onRefreshed(newAccessToken);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        }
        return apiClient(originalRequest);
      } catch {
        isRefreshing = false;
        refreshSubscribers = [];
        clearTokens();
        onSessionExpired?.();
        return Promise.reject(error);
      }
    }

    // 401 without refresh token — session expired
    if (error.response?.status === 401) {
      clearTokens();
      onSessionExpired?.();
    }

    return Promise.reject(error);
  }
);

/**
 * Extract a user-friendly error message from an API error.
 */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (data && typeof data === 'object' && 'detail' in data) {
      return String(data.detail);
    }
    if (error.response?.status === 0 || error.code === 'ERR_NETWORK') {
      return 'Unable to reach the server. Check your connection.';
    }
    if (error.response?.status === 503) {
      return 'Service temporarily unavailable. Please try again.';
    }
    return error.message || 'An unexpected error occurred.';
  }
  if (error instanceof Error) return error.message;
  return 'An unexpected error occurred.';
}
