import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import api, { onSessionExpired, errorMessage } from '@/api';
import { tokens } from '@/api/tokens';
import { StaffUser } from '@/lib/rentals';

const Context = createContext<{
  user: StaffUser | null; loading: boolean; error: string; reconnect(): Promise<void>;
  signIn(login: string, password: string): Promise<void>; signOut(): Promise<void>;
}>({ user: null, loading: true, error: '', reconnect: async () => {}, signIn: async () => {}, signOut: async () => {} });

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<StaffUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const reconnect = useCallback(async () => {
    setLoading(true); setError('');
    try { if (await tokens.access()) setUser((await api.get('/me/')).data); }
    catch (failure) { setError(errorMessage(failure)); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { const remove = onSessionExpired(() => setUser(null)); void reconnect(); return remove; }, [reconnect]);
  const signIn = async (login: string, password: string) => {
    const { data } = await api.post('/auth/login/', { login: login.trim(), password });
    await tokens.save(data.access, data.refresh);
    setUser((await api.get('/me/')).data); setError('');
  };
  const signOut = async () => {
    const { disconnectReminders } = await import('@/lib/notifications');
    try {
      await disconnectReminders(user?.id);
      const refresh = await tokens.refresh();
      if (refresh) await api.post('/auth/logout/', { refresh });
    } finally { await tokens.clear(); setUser(null); }
  };
  return <Context.Provider value={{ user, loading, error, reconnect, signIn, signOut }}>{children}</Context.Provider>;
}
export const useSession = () => useContext(Context);
