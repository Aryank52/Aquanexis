/// <reference types="vite/client" />

interface ImportMetaEnv {
  VITE_API_BASE_URL?: string;
  VITE_AUTH_DISABLED?: string;
  // Add other VITE_ environment variables as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
