import React, { useCallback, useState } from 'react';
import { Text, View } from 'react-native';
import { router, useFocusEffect } from 'expo-router';
import api, { errorMessage } from '@/api';
import { useSession } from '@/providers/session';
import { useReminders } from '@/providers/reminders';
import { Board, nepalDate } from '@/lib/rentals';
import { Button, Notice, RentalCard, Screen, palette, ui } from '@/components/staff-ui';

export default function Today() {
  const { user } = useSession();
  const reminders = useReminders();
  const [board, setBoard] = useState<Board | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    setBusy(true); setError('');
    try { setBoard((await api.get('/rental-board/')).data); }
    catch (failure) { setError(errorMessage(failure)); }
    finally { setBusy(false); }
  }, []);
  useFocusEffect(useCallback(() => { void load(); const timer = setInterval(() => void load(), 60000); return () => clearInterval(timer); }, [load]));
  return <Screen refreshing={busy} onRefresh={() => void load()}>
    <Text style={ui.eyebrow}>EASYMOTO Â· {nepalDate()} Â· NEPAL TIME</Text>
    <Text style={ui.title}>Today, under control.</Text><Text style={ui.subtitle}>Welcome back, {user?.full_name}. Hereâ€™s what needs your teamâ€™s attention.</Text>
    <Button title="New rental" icon="add" onPress={() => router.push('/create-customer')} />
    <Notice text={error} error />
    {board && <>
      <View style={ui.row}>{[['Overdue', board.overdue], ['Due today', board.due_today], ['On rent', board.on_rent]].map(([label, number]) => <View key={label} style={ui.metric}><Text style={[ui.metricValue, label === 'Overdue' && Number(number) > 0 && { color: palette.red }]}>{number}</Text><Text style={ui.subtitle}>{label}</Text></View>)}</View>
      <View style={ui.card}><Text style={ui.heading}>{board.pickups_today} pickups today</Text><Text style={ui.subtitle}>{board.upcoming} upcoming rentals Â· {board.pending} awaiting confirmation</Text><Button title="View all rentals" secondary onPress={() => router.push('/(tabs)/bookings')} /></View>
      <View style={ui.row}><Text style={ui.heading}>Return queue</Text><Text style={ui.subtitle}>Overdue + next 24 hours</Text></View>
      {board.alerts.length ? board.alerts.slice(0, 10).map(rental => <RentalCard key={rental.id} rental={rental} />) : <View style={ui.card}><Text style={ui.heading}>No returns need attention.</Text><Text style={ui.subtitle}>Upcoming return reminders will appear here.</Text></View>}
    </>}
    {!board && !busy && <Button title="Try again" onPress={() => void load()} secondary />}
    <View style={ui.card}><Text style={ui.heading}>Keep the team in the loop</Text><Text style={ui.subtitle}>Enable phone reminders for upcoming returns. WhatsApp drafts are ready inside each rental.</Text><Notice text={reminders.message} /><Button title="Enable phone reminders" icon="notifications-outline" busy={reminders.busy} onPress={() => void reminders.sync(true)} secondary /></View>
  </Screen>;
}
