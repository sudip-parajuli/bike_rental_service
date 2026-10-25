import React, { useState } from 'react';
import { Text, View } from 'react-native';
import { useSession } from '@/providers/session';
import { useReminders } from '@/providers/reminders';
import { Button, Notice, Screen, confirmAction, ui } from '@/components/staff-ui';
import { errorMessage } from '@/api';

export default function Account() {
  const { user, signOut } = useSession();
  const reminders = useReminders();
  const [error, setError] = useState('');
  return <Screen><Text style={ui.eyebrow}>YOUR WORKSPACE</Text><Text style={ui.title}>Account & reminders</Text>
    <View style={ui.card}><Text style={ui.heading}>{user?.full_name}</Text><Text style={ui.subtitle}>{user?.username} Â· {user?.is_superuser ? 'Owner / administrator' : 'Staff'}</Text><Text style={ui.subtitle}>{user?.email}</Text></View>
    <View style={ui.card}><Text style={ui.heading}>Phone reminders</Text><Text style={ui.subtitle}>Returns use Nepal time, even when your phone is set to another timezone. Server reminders need a configured scheduler and push credentials.</Text><Notice text={reminders.message} /><Button title="Enable or refresh reminders" onPress={() => void reminders.sync(true)} busy={reminders.busy} icon="notifications-outline" /><Button title="Disable on this phone" secondary onPress={() => void reminders.disable()} busy={reminders.busy} /></View>
    <Notice text={error} error /><Button title="Sign out" secondary onPress={async () => { if (await confirmAction('Sign out?', 'Your saved phone reminders will be cleared.')) { try { await signOut(); } catch (failure) { setError(errorMessage(failure)); } } }} />
    <Text style={ui.subtitle}>EasyMoto Operations Â· Android & iPhone</Text>
  </Screen>;
}
