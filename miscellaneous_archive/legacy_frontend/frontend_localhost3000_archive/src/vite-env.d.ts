/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_WS_URL: string;
  readonly VITE_APP_NAME: string;
  readonly VITE_APP_VERSION: string;
  readonly VITE_ENABLE_PWA: string;
  readonly VITE_ENABLE_WEBSOCKET: string;
  readonly VITE_ENABLE_NOTIFICATIONS: string;
  readonly VITE_SENTRY_DSN: string;
  readonly VITE_SENTRY_ENVIRONMENT: string;
  readonly VITE_STORAGE_KEY: string;
  readonly VITE_SESSION_TIMEOUT: string;
  readonly VITE_SESSION_WARNING_TIME: string;
  readonly VITE_DEFAULT_ASSET: string;
  readonly VITE_REFRESH_INTERVAL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare const __APP_VERSION__: string;
