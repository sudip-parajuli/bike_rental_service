import React, { useCallback, useState } from 'react';
import { Image, Text, View } from 'react-native';
import { router, useFocusEffect } from 'expo-router';
import api, { errorMessage, BASE_MEDIA_URL } from '@/api';
import { Vehicle, listResults, money } from '@/lib/rentals';
import { Button, Field, Notice, Screen, ui } from '@/components/staff-ui';
export default function Fleet() {
  const [items, setItems] = useState<Vehicle[]>([]); const [query, setQuery] = useState('');
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const [page, setPage] = useState(1); const [more, setMore] = useState(false);
  const load = useCallback(async (next = 1) => {
    setBusy(true); setError('');
    try { const { data } = await api.get('/bikes/', { params: { page: next } }); setItems(previous => next === 1 ? listResults<Vehicle>(data) : [...previous, ...listResults<Vehicle>(data)]); setPage(next); setMore(!!data.next); }
    catch (failure) { setError(errorMessage(failure)); } finally { setBusy(false); }
  }, []);
  useFocusEffect(useCallback(() => { void load(); }, [load]));
  return <Screen refreshing={busy} onRefresh={() => void load()}><Text style={ui.eyebrow}>THE FLEET</Text><Text style={ui.title}>Ready for the next ride.</Text><Field label="Filter loaded vehicles" value={query} onChangeText={setQuery} /><Notice text={error} error />
    {items.filter(value => (value.name + value.vehicle_number).toLowerCase().includes(query.toLowerCase())).map(vehicle => <View key={vehicle.id} style={ui.card}>
      {vehicle.image_url && <Image accessibilityLabel={vehicle.name} source={{ uri: vehicle.image_url.startsWith('http') ? vehicle.image_url : BASE_MEDIA_URL + vehicle.image_url }} resizeMode="contain" style={{ height: 170, borderRadius: 14 }} />}
      <View style={ui.row}><Text style={ui.heading}>{vehicle.name}</Text><Text style={ui.subtitle}>{money(vehicle.price_per_day)} / day</Text></View>
      <Text style={ui.subtitle}>{vehicle.vehicle_number || 'Plate not recorded'} Â· {vehicle.availability_status && vehicle.is_approved ? 'In service' : 'Unavailable'}</Text>
      <Button title="Vehicle details & maintenance" secondary onPress={() => router.push({ pathname: '/bike/[id]', params: { id: vehicle.id } })} />
    </View>)}
    {more && <Button title="Load more vehicles" secondary busy={busy} onPress={() => void load(page + 1)} />}
  </Screen>;
}
