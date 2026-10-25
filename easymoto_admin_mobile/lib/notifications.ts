import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import api from '@/api';
import { listResults, Rental, StaffUser } from './rentals';

export async function syncReminders(user: StaffUser, requestPermission = false): Promise<string> {
  if (Platform.OS === 'web') return 'Phone reminders require an Android or iPhone build. The in-app return queue is available here.';
  const Notifications = await import('expo-notifications');
  if (Platform.OS === 'android') await Notifications.setNotificationChannelAsync('rentals', { name: 'Rental returns', importance: Notifications.AndroidImportance.HIGH });
  let permissions = await Notifications.getPermissionsAsync();
  if (!permissions.granted && requestPermission) permissions = await Notifications.requestPermissionsAsync();
  if (!permissions.granted) return 'Notifications are not allowed. Enable them in your phone settings to receive reminders.';
  if (requestPermission) await AsyncStorage.setItem(`rental_reminders_${user.id}`, 'true');
  if (await AsyncStorage.getItem(`rental_reminders_${user.id}`) !== 'true') return 'Reminders are off on this phone.';
  Notifications.setNotificationHandler({ handleNotification: async () => ({ shouldPlaySound: true, shouldSetBadge: false, shouldShowBanner: true, shouldShowList: true }) });
  if (user.reminders_enabled && Constants.executionEnvironment !== 'storeClient') {
    try {
      const projectId = Constants.expoConfig?.extra?.eas?.projectId || Constants.easConfig?.projectId;
      if (projectId) {
        const token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;
        await api.post('/devices/', { token, platform: Platform.OS });
        await AsyncStorage.setItem('rental_push_token', token);
        await Notifications.cancelAllScheduledNotificationsAsync();
        return 'Server push reminders enabled on this phone. Delivery needs the scheduler and native push credentials.';
      }
    } catch { /* Keep the free, on-device fallback available when push is not configured. */ }
  }
  const response = await api.get('/rentals/', { params: { status: 'confirmed', page_size: 100 } });
  const rentals = listResults<Rental>(response.data).filter(rental => Date.parse(rental.end_date) > Date.now()).slice(0, 20);
  await Notifications.cancelAllScheduledNotificationsAsync();
  for (const rental of rentals) {
    for (const hours of [24, 3, 0]) {
      const at = Date.parse(rental.end_date) - hours * 3600000;
      if (at <= Date.now()) continue;
      await Notifications.scheduleNotificationAsync({
        identifier: `rental-${rental.id}-${hours}`,
        content: { title: hours === 0 ? 'Rental return is due' : 'Upcoming rental return', body: `Rental #${rental.id}: open EasyMoto to review the return.`, data: { booking_id: rental.id }, sound: 'default' },
        trigger: { type: Notifications.SchedulableTriggerInputTypes.DATE, date: new Date(at), channelId: 'rentals' },
      });
    }
  }
  return 'Phone reminders enabled for up to 20 upcoming returns. Open the app to sync date changes made by other staff; server push needs additional setup.';
}

export async function disconnectReminders(userId?: number) {
  const token = await AsyncStorage.getItem('rental_push_token');
  try { if (token) await api.delete('/devices/', { data: { token } }); }
  finally {
    if (Platform.OS !== 'web') await (await import('expo-notifications')).cancelAllScheduledNotificationsAsync();
    if (userId) await AsyncStorage.removeItem(`rental_reminders_${userId}`);
  }
  await AsyncStorage.removeItem('rental_push_token');
}
