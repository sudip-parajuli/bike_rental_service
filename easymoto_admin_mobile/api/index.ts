import { createStaffClient } from './client';
import { tokens } from './tokens';

// This public build setting is an API address, never a credential.
export const API_URL = (process.env.EXPO_PUBLIC_API_URL || 'https://www.easymoto.com.np/api/mobile').replace(/\/$/, '');
export const BASE_MEDIA_URL = API_URL.replace(/\/api\/mobile$/, '');
const listeners = new Set<() => void>();
export function onSessionExpired(listener: () => void) { listeners.add(listener); return () => { listeners.delete(listener); }; }
const api = createStaffClient(API_URL, tokens, () => listeners.forEach(listener => listener()));
export { errorMessage } from './client';
export default api;
