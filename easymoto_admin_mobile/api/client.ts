import axios, { AxiosError, InternalAxiosRequestConfig, create, isAxiosError } from 'axios';

export interface TokenStore {
  access(): Promise<string | null>;
  refresh(): Promise<string | null>;
  save(access: string, refresh: string): Promise<void>;
  clear(): Promise<void>;
}

export function createStaffClient(baseURL: string, store: TokenStore, expired: () => void) {
  const client = create({ baseURL, timeout: 75000, headers: { 'Content-Type': 'application/json' } });
  let refreshing: Promise<string> | null = null;
  client.interceptors.request.use(async config => {
    const token = await store.access();
    if (token && !config.url?.includes('/auth/')) config.headers.Authorization = `Bearer ${token}`;
    return config;
  });
  client.interceptors.response.use(response => response, async (error: AxiosError) => {
    const config = error.config as (InternalAxiosRequestConfig & { retried?: boolean }) | undefined;
    if (error.response?.status !== 401 || !config || config.url?.includes('/auth/')) throw error;
    if (config.retried) {
      await store.clear(); expired(); throw error;
    }
    config.retried = true;
    if (!refreshing) {
      refreshing = (async () => {
        const refresh = await store.refresh();
        if (!refresh) { await store.clear(); expired(); throw error; }
        try {
          const response = await axios.post(`${baseURL}/auth/refresh/`, { refresh }, { timeout: 75000 });
          await store.save(response.data.access, response.data.refresh || refresh);
          return response.data.access as string;
        } catch (failure) {
          if (isAxiosError(failure) && [400, 401, 403].includes(failure.response?.status || 0)) {
            await store.clear(); expired();
          }
          // A disconnected server is not a reason to erase a valid session.
          throw failure;
        }
      })().finally(() => { refreshing = null; });
    }
    const access = await refreshing;
    config.headers.Authorization = `Bearer ${access}`;
    return client(config);
  });
  return client;
}

export function errorMessage(error: unknown): string {
  if (!isAxiosError(error)) return error instanceof Error ? error.message : 'Something went wrong. Please try again.';
  if (error.response?.status === 409) return 'Another staff member changed this rental. Refresh it before saving.';
  if (!error.response) return 'Cannot reach EasyMoto. Check your connection and try again.';
  if (error.response.status >= 500) return 'The server is unavailable. Please try again shortly.';
  const data = error.response.data;
  if (typeof data === 'object' && data) {
    return Object.entries(data).map(([key, value]) => `${key === 'detail' || key === 'non_field_errors' ? '' : `${key.replaceAll('_', ' ')}: `}${Array.isArray(value) ? value.join(' ') : String(value)}`).join('\n');
  }
  return 'Your request could not be completed. Please try again.';
}
