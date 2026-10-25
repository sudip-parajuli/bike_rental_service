import React from 'react';
import { ActivityIndicator, Text, View } from 'react-native';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SessionProvider, useSession } from '@/providers/session';
import { RemindersProvider } from '@/providers/reminders';
import { palette } from '@/components/staff-ui';
import 'react-native-reanimated';

function Navigation() {
  const { user, loading } = useSession();
  if (loading) return <View style={{ flex: 1, gap: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.background }}><ActivityIndicator size="large" color={palette.blue} /><Text style={{ color: palette.muted }}>Connecting to EasyMoto…</Text></View>;
  return <RemindersProvider><Stack screenOptions={{ headerTintColor: palette.ink, headerShadowVisible: false, headerStyle: { backgroundColor: palette.background }, contentStyle: { backgroundColor: palette.background } }}>
    <Stack.Protected guard={!user}><Stack.Screen name="index" options={{ headerShown: false }} /></Stack.Protected>
    <Stack.Protected guard={!!user}>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="booking/[id]" options={{ title: 'Rental details' }} />
      <Stack.Screen name="create-walkin-booking" options={{ title: 'New rental' }} />
      <Stack.Screen name="create-customer" options={{ title: 'Customer details' }} />
      <Stack.Screen name="bike/[id]" options={{ title: 'Vehicle details' }} />
      <Stack.Screen name="bike/add-maintenance" options={{ title: 'Maintenance' }} />
      <Stack.Screen name="modal" options={{ presentation: 'modal' }} />
    </Stack.Protected>
  </Stack></RemindersProvider>;
}
export default function RootLayout() { return <SessionProvider><Navigation /><StatusBar style="dark" /></SessionProvider>; }
