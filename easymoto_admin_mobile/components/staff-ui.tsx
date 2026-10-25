import React from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View, RefreshControl, Platform, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { displayDate, labels, money, Rental } from '@/lib/rentals';

export const palette = { ink: '#16263B', muted: '#66768A', blue: '#2454E6', background: '#F4F6FA', line: '#E2E8F0', red: '#B42318', green: '#087F5B' };
export const ui = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.background },
  content: { padding: 20, gap: 16, paddingBottom: 36, width: '100%', maxWidth: 960, alignSelf: 'center', flexGrow: 1 },
  title: { fontSize: 30, fontWeight: '800', color: palette.ink, letterSpacing: -1 },
  subtitle: { fontSize: 14, color: palette.muted, lineHeight: 22 },
  eyebrow: { fontSize: 11, fontWeight: '700', letterSpacing: 2, color: palette.blue, textTransform: 'uppercase' },
  card: { backgroundColor: '#FFF', borderRadius: 20, padding: 20, gap: 12, borderWidth: 1, borderColor: palette.line },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' },
  heading: { fontSize: 18, fontWeight: '700', color: palette.ink },
  label: { fontSize: 13, fontWeight: '600', color: palette.ink, marginBottom: 6 },
  input: { backgroundColor: '#FFF', color: palette.ink, borderWidth: 1, borderColor: '#CFD8E5', borderRadius: 12, padding: 14, fontSize: 16, minHeight: 48 },
  field: { gap: 4, flexGrow: 1 },
  metric: { flexGrow: 1, flexBasis: '28%', minWidth: 90, padding: 16, borderRadius: 16, backgroundColor: '#FFF', borderWidth: 1, borderColor: palette.line },
  metricValue: { fontSize: 30, fontWeight: '800', color: palette.ink },
  badge: { alignSelf: 'flex-start', borderRadius: 30, paddingHorizontal: 10, paddingVertical: 6, backgroundColor: '#EDF2FF' },
  badgeText: { fontSize: 12, fontWeight: '700', color: palette.blue },
});
export function Screen({ children, refreshing = false, onRefresh }: { children: React.ReactNode; refreshing?: boolean; onRefresh?: () => void }) {
  return <SafeAreaView style={ui.screen}><ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={ui.content} refreshControl={onRefresh ? <RefreshControl refreshing={refreshing} onRefresh={onRefresh} /> : undefined}>{children}</ScrollView></SafeAreaView>;
}
export function Button({ title, onPress, busy = false, disabled = false, secondary = false, danger = false, icon }: { title: string; onPress(): void; busy?: boolean; disabled?: boolean; secondary?: boolean; danger?: boolean; icon?: React.ComponentProps<typeof Ionicons>['name'] }) {
  const color = danger ? palette.red : palette.blue;
  return <Pressable accessibilityRole="button" accessibilityLabel={title} disabled={disabled || busy} onPress={onPress} style={({ pressed }) => ({ minHeight: 48, paddingVertical: 13, paddingHorizontal: 18, borderRadius: 12, backgroundColor: secondary ? '#EDF2FF' : color, opacity: disabled || busy ? .5 : pressed ? .8 : 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 })}>
    {busy ? <ActivityIndicator color={secondary ? color : '#FFF'} /> : <>{icon && <Ionicons name={icon} size={19} color={secondary ? color : '#FFF'} />}<Text style={{ fontSize: 14, fontWeight: '700', color: secondary ? color : '#FFF' }}>{title}</Text></>}
  </Pressable>;
}
export function Field({ label, ...props }: React.ComponentProps<typeof TextInput> & { label: string }) {
  return <View style={ui.field}><Text style={ui.label}>{label}</Text><TextInput accessibilityLabel={label} placeholderTextColor="#8A96A8" {...props} style={[ui.input, props.style]} /></View>;
}
export function Notice({ text, error = false }: { text: string; error?: boolean }) {
  if (!text) return null;
  return <View accessibilityRole="alert" style={{ backgroundColor: error ? '#FEF0EE' : '#EDF2FF', padding: 14, borderRadius: 12 }}><Text style={{ color: error ? palette.red : palette.ink, fontSize: 14, lineHeight: 21 }}>{text}</Text></View>;
}
export function Badge({ state }: { state: string }) {
  return <View style={[ui.badge, state === 'overdue' && { backgroundColor: '#FEE4E2' }]}><Text style={[ui.badgeText, state === 'overdue' && { color: palette.red }]}>{labels[state] || state}</Text></View>;
}
export function RentalCard({ rental }: { rental: Rental }) {
  return <Pressable accessibilityRole="button" accessibilityLabel={`Open rental ${rental.id} for ${rental.bike_name}`} onPress={() => router.push({ pathname: '/booking/[id]', params: { id: rental.id } })} style={ui.card}>
    <View style={ui.row}><Text style={ui.eyebrow}>Rental #{rental.id}</Text><Badge state={rental.due_state} /></View>
    <Text style={ui.heading}>{rental.bike_name}</Text><Text style={ui.subtitle}>{rental.customer_name || 'Customer'} · {rental.customer_phone || 'No phone'}</Text>
    <Text style={{ color: palette.ink, fontWeight: '600' }}>Return: {displayDate(rental.end_date)}</Text>
    <View style={ui.row}><Text style={ui.subtitle}>Nepal time</Text><Text style={{ color: Number(rental.balance_due) > 0 ? palette.red : palette.green, fontWeight: '700' }}>{Number(rental.balance_due) > 0 ? `${money(rental.balance_due)} due` : 'Paid'}</Text></View>
  </Pressable>;
}
export function confirmAction(title: string, message: string): Promise<boolean> {
  if (Platform.OS === 'web') return Promise.resolve(window.confirm(`${title}\n\n${message}`));
  return new Promise(resolve => Alert.alert(title, message, [{ text: 'Cancel', style: 'cancel', onPress: () => resolve(false) }, { text: 'Confirm', onPress: () => resolve(true) }], { cancelable: true, onDismiss: () => resolve(false) }));
}
