import React, { useCallback, useState } from 'react';
import { Text, View } from 'react-native';
import { router, useFocusEffect } from 'expo-router';
import api, { errorMessage } from '@/api';
import { listResults } from '@/lib/rentals';
import { Button, Field, Notice, Screen, ui } from '@/components/staff-ui';
interface Customer { id: number; full_name: string; username: string; phone_number: string; email: string; booking_count: number; }
export default function Customers() {
  const [items, setItems] = useState<Customer[]>([]); const [query, setQuery] = useState('');
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const [page, setPage] = useState(1); const [more, setMore] = useState(false);
  const load = useCallback(async (next = 1) => {
    setBusy(true); setError('');
    try { const { data } = await api.get('/customers/', { params: { page: next } }); setItems(previous => next === 1 ? listResults<Customer>(data) : [...previous, ...listResults<Customer>(data)]); setPage(next); setMore(!!data.next); }
    catch (failure) { setError(errorMessage(failure)); } finally { setBusy(false); }
  }, []);
  useFocusEffect(useCallback(() => { void load(); }, [load]));
  return <Screen refreshing={busy} onRefresh={() => void load()}><Text style={ui.eyebrow}>CUSTOMERS</Text><Text style={ui.title}>People behind the rides.</Text><Button title="Find or add customer" icon="person-add-outline" onPress={() => router.push('/create-customer')} /><Field label="Filter loaded customers" value={query} onChangeText={setQuery} /><Notice text={error} error />
    {items.filter(value => ((value.full_name || value.username || '') + value.phone_number).toLowerCase().includes(query.toLowerCase())).map(customer => <View key={customer.id} style={ui.card}><Text style={ui.heading}>{customer.full_name || customer.username}</Text><Text style={ui.subtitle}>{customer.phone_number || 'No phone number'}</Text><Text style={ui.subtitle}>{customer.email}</Text><Button title="Create rental for customer" secondary disabled={!customer.phone_number} onPress={() => router.push({ pathname: '/create-walkin-booking', params: { phone: customer.phone_number } })} /></View>)}
    {more && <Button title="Load more customers" secondary busy={busy} onPress={() => void load(page + 1)} />}
  </Screen>;
}
