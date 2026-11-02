import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from './state/theme';

import { App } from './app/App';
import './styles/globals.css';

// Create QueryClient with default options aligned to data fetching strategy
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5_000, // 5 seconds — live telemetry
      gcTime: 60_000, // 1 minute garbage collection
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors (auth failures, not found, etc.)
        if (error && typeof error === 'object' && 'response' in error) {
          const status = (error as { response?: { status?: number } }).response?.status;
          if (status && status >= 400 && status < 500) return false;
        }
        return failureCount < 3;
      },
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: false,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
