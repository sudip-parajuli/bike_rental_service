import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { AppState, Platform } from 'react-native';
import { router } from 'expo-router';
import { useSession } from './session';
import { syncReminders, disconnectReminders } from '@/lib/notifications';
import { errorMessage } from '@/api';

const Context = createContext({ message: '', busy: false, sync: async (_request = false) => {}, disable: async () => {} });
export function RemindersProvider({ children }: { children: React.ReactNode }) {
  const { user } = useSession();
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const sync = useCallback(async (request = false) => {
    if (!user) return;
    setBusy(true);
    try { setMessage(await syncReminders(user, request)); }
    catch (failure) { setMessage(errorMessage(failure)); }
    finally { setBusy(false); }
  }, [user]);
  const disable = async () => {
    if (!user) return;
    setBusy(true);
    try { await disconnectReminders(user.id); setMessage('Reminders disabled on this phone.'); }
    catch (failure) { setMessage(errorMessage(failure)); }
    finally { setBusy(false); }
  };
  useEffect(() => {
    if (!user) return;
    void sync();
    const subscription = AppState.addEventListener('change', state => { if (state === 'active') void sync(); });
    return () => subscription.remove();
  }, [user, sync]);
  useEffect(() => {
    if (!user || Platform.OS === 'web') return;
    let cleanup = () => {};
    let cancelled = false;
    void import('expo-notifications').then(async Notifications => {
      if (cancelled) return;
      const open = (response: import('expo-notifications').NotificationResponse | null) => {
        const id = response?.notification.request.content.data.booking_id;
        if (typeof id === 'number' && Number.isSafeInteger(id) && id > 0) router.push({ pathname: '/booking/[id]', params: { id } });
      };
      const listener = Notifications.addNotificationResponseReceivedListener(open);
      cleanup = () => listener.remove();
      open(await Notifications.getLastNotificationResponseAsync());
    });
    return () => { cancelled = true; cleanup(); };
  }, [user]);
  return <Context.Provider value={{ message, busy, sync, disable }}>{children}</Context.Provider>;
}
export const useReminders = () => useContext(Context);
