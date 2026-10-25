import React, { useState } from 'react';
import { KeyboardAvoidingView, Platform, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSession } from '@/providers/session';
import { errorMessage } from '@/api';
import { Button, Field, Notice, Screen, palette, ui } from '@/components/staff-ui';

export default function Login() {
  const session = useSession();
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const signIn = async () => {
    if (!login.trim() || !password) { setError('Enter your username or email and password.'); return; }
    setBusy(true); setError('');
    try { await session.signIn(login, password); }
    catch (failure) { setError(errorMessage(failure)); }
    finally { setBusy(false); }
  };
  return <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}><Screen>
    <View style={{ flex: 1, justifyContent: 'center', gap: 24, maxWidth: 440, width: '100%', alignSelf: 'center' }}>
      <View style={{ width: 64, height: 64, borderRadius: 20, backgroundColor: palette.blue, alignItems: 'center', justifyContent: 'center' }}><Ionicons name="bicycle" size={36} color="#FFF" /></View>
      <View><Text style={ui.eyebrow}>EASYMOTO Â· OPERATIONS</Text><Text style={[ui.title, { fontSize: 40, marginTop: 12 }]}>A clearer day{ '\n' }at the rental desk.</Text><Text style={[ui.subtitle, { marginTop: 12 }]}>Bookings, returns and reminders. One workspace for your team.</Text></View>
      <View style={ui.card}>
        <Text style={ui.heading}>Staff sign in</Text><Notice text={error || session.error} error />
        {busy && <Notice text="Connecting to your workspace. The first connection may take about a minute." />}
        <Field label="Username or email" value={login} onChangeText={setLogin} autoCapitalize="none" autoCorrect={false} autoComplete="username" />
        <Field label="Password" value={password} onChangeText={setPassword} secureTextEntry autoComplete="current-password" onSubmitEditing={() => void signIn()} />
        <Button title="Sign in" onPress={() => void signIn()} busy={busy} icon="arrow-forward" />
        {!!session.error && <Button title="Reconnect existing session" onPress={() => void session.reconnect()} secondary />}
      </View>
      <Text style={ui.subtitle}>For active EasyMoto staff and administrators. Use the same account as your website staff login.</Text>
    </View>
  </Screen></KeyboardAvoidingView>;
}
