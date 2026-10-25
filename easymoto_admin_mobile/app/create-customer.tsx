import React, { useState } from 'react';
import { Text, View } from 'react-native';
import { router } from 'expo-router';
import api, { errorMessage } from '@/api';
import { Button, Field, Notice, Screen, ui } from '@/components/staff-ui';

export default function CustomerForm() {
  const [phone, setPhone] = useState(''); const [name, setName] = useState('');
  const [email, setEmail] = useState(''); const [nationality, setNationality] = useState('Nepali');
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const next = (value: string) => router.push({ pathname: '/create-walkin-booking', params: { phone: value } });
  const find = async () => {
    if (!phone.trim()) { setError('Enter the customer phone number.'); return; }
    setBusy(true); setError('');
    try { const { data } = await api.get('/customers/walk-in/', { params: { phone } }); next(data.phone_number); }
    catch (failure) { setError(errorMessage(failure)); } finally { setBusy(false); }
  };
  const create = async () => {
    if (!phone.trim() || !name.trim()) { setError('Customer name and phone number are required.'); return; }
    setBusy(true); setError('');
    try { const { data } = await api.post('/customers/walk-in/', { phone_number: phone, full_name: name, email, nationality }); next(data.phone_number); }
    catch (failure) { setError(errorMessage(failure)); } finally { setBusy(false); }
  };
  return <Screen><Text style={ui.eyebrow}>NEW RENTAL Â· STEP 1 OF 2</Text><Text style={ui.title}>Whoâ€™s riding?</Text>
    <Text style={ui.subtitle}>Find a returning customer by phone, or add their details below. Include the country code for international numbers.</Text>
    <Notice text={error} error />
    <View style={ui.card}><Field label="Customer phone number" value={phone} onChangeText={setPhone} keyboardType="phone-pad" placeholder="+977 98â€¦" /><Button title="Find existing customer" secondary busy={busy} onPress={() => void find()} /></View>
    <View style={ui.card}><Text style={ui.heading}>New customer</Text>
      <Field label="Full name" value={name} onChangeText={setName} />
      <Field label="Email (optional, for return reminders)" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" />
      <Field label="Nationality" value={nationality} onChangeText={setNationality} />
      <Button title="Continue to vehicle & dates" busy={busy} onPress={() => void create()} icon="arrow-forward" />
    </View>
  </Screen>;
}
