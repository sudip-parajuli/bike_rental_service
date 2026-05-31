import { DarkTheme, DefaultTheme, ThemeProvider } from '@react-navigation/native';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import 'react-native-reanimated';

import { useColorScheme } from '@/hooks/use-color-scheme';

export const unstable_settings = {
  anchor: '(tabs)',
};

export default function RootLayout() {
  const colorScheme = useColorScheme();

  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <Stack>
        <Stack.Screen name="index" options={{ headerShown: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="modal" options={{ presentation: 'modal', title: 'Modal' }} />
        <Stack.Screen name="create-walkin-booking" options={{ title: 'Create Walk-in Booking' }} />
        <Stack.Screen name="create-customer" options={{ title: 'Add Customer' }} />
        <Stack.Screen name="bike/[id]" options={{ title: 'Bike Details' }} />
        <Stack.Screen name="bike/add-maintenance" options={{ title: 'Add Maintenance Record' }} />
      </Stack>
      <StatusBar style="auto" />
    </ThemeProvider>
  );
}
