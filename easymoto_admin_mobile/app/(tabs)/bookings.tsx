import React, { useCallback, useState } from 'react';
import { Pressable, ScrollView, Text, View } from 'react-native';
import { useFocusEffect, useLocalSearchParams } from 'expo-router';
import api, { errorMessage } from '@/api';
import { Rental, listResults } from '@/lib/rentals';
import { Button, Field, Notice, RentalCard, Screen, palette, ui } from '@/components/staff-ui';

const filters = [['active', 'On rent'], ['overdue', 'Overdue'], ['today', 'Due today'], ['upcoming', 'Upcoming'], ['pending', 'Pending'], ['completed', 'Returned'], ['all', 'All']];
export default function Rentals() {
  const params = useLocalSearchParams<{ filter?: string }>();
  const [filter, setFilter] = useState(params.filter || 'active');
  const [search, setSearch] = useState('');
  const [query, setQuery] = useState('');
  const [items, setItems] = useState<Rental[]>([]);
  const [page, setPage] = useState(1);
  const [more, setMore] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const load = useCallback(async (nextPage = 1) => {
    setBusy(true); setError('');
    const params: Record<string, string | number> = { page: nextPage, search: query };
    if (['active', 'overdue', 'today', 'upcoming'].includes(filter)) params.due = filter;
    else if (filter !== 'all') params.status = filter;
    try {
      const { data } = await api.get('/rentals/', { params });
      const incoming = listResults<Rental>(data);
      setItems(previous => nextPage === 1 ? incoming : [...previous, ...incoming]);
      setPage(nextPage); setMore(!!data.next);
    } catch (failure) { setError(errorMessage(failure)); }
    finally { setBusy(false); }
  }, [filter, query]);
  useFocusEffect(useCallback(() => { void load(); }, [load]));
  return <Screen refreshing={busy && page === 1} onRefresh={() => void load()}>
    <Text style={ui.eyebrow}>RENTAL DESK</Text><Text style={ui.title}>Every rental. One place.</Text>
    <Field label="Search customer, phone or vehicle" value={search} onChangeText={setSearch} onSubmitEditing={() => setQuery(search.trim())} returnKeyType="search" />
    <Button title="Search rentals" secondary onPress={() => setQuery(search.trim())} />
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8 }}>{filters.map(([key, title]) => <Pressable key={key} onPress={() => setFilter(key)} accessibilityRole="button" accessibilityState={{ selected: key === filter }} style={{ padding: 12, borderRadius: 24, backgroundColor: key === filter ? palette.ink : '#FFF', borderWidth: 1, borderColor: palette.line }}><Text style={{ color: key === filter ? '#FFF' : palette.muted, fontWeight: '600' }}>{title}</Text></Pressable>)}</ScrollView>
    <Notice text={error} error />
    {items.map(rental => <RentalCard key={rental.id} rental={rental} />)}
    {!items.length && !busy && <View style={ui.card}><Text style={ui.heading}>{error ? 'Unable to load rentals.' : 'No rentals match this view.'}</Text><Text style={ui.subtitle}>Choose another filter or search again.</Text></View>}
    {more && <Button title="Load more rentals" secondary busy={busy} onPress={() => void load(page + 1)} />}
  </Screen>;
}
