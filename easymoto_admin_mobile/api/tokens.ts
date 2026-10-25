import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

async function read(key: string) {
  if (Platform.OS === 'web') return typeof sessionStorage === 'undefined' ? null : sessionStorage.getItem(key);
  const secure = await SecureStore.getItemAsync(key);
  if (secure) return secure;
  const legacy = await AsyncStorage.getItem(key);
  if (legacy) { await SecureStore.setItemAsync(key, legacy); await AsyncStorage.removeItem(key); }
  return legacy;
}
async function write(key: string, value: string) {
  if (Platform.OS === 'web') { sessionStorage.setItem(key, value); return; }
  await SecureStore.setItemAsync(key, value);
}
export const tokens = {
  access: () => read('access_token'),
  refresh: () => read('refresh_token'),
  save: async (access: string, refresh: string) => {
    await write('refresh_token', refresh); await write('access_token', access);
  },
  clear: async () => {
    if (Platform.OS === 'web') { sessionStorage.removeItem('access_token'); sessionStorage.removeItem('refresh_token'); }
    else { await SecureStore.deleteItemAsync('access_token'); await SecureStore.deleteItemAsync('refresh_token'); }
    await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'is_staff', 'is_superuser', 'username', 'full_name', 'email']);
  },
};
