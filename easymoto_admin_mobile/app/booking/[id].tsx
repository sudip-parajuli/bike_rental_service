import React, { useCallback, useState } from 'react';
import { Linking, Switch, Text, View } from 'react-native';
import { useFocusEffect, useLocalSearchParams } from 'expo-router';
import api, { errorMessage } from '@/api';
import { Rental, displayDate, money, nepalDate, nepalTime, rentalDateTime } from '@/lib/rentals';
import { openRentalDocument } from '@/lib/documents';
import { useReminders } from '@/providers/reminders';
import { Badge, Button, Field, Notice, Screen, confirmAction, ui } from '@/components/staff-ui';
import { RentalDate } from '@/components/rental-date';

export default function RentalDetails() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const reminders = useReminders();
  const [rental, setRental] = useState<Rental | null>(null);
  const [start, setStart] = useState(''); const [end, setEnd] = useState('');
  const [pickupTime, setPickupTime] = useState('09:00'); const [returnTime, setReturnTime] = useState('19:00');
  const [notes, setNotes] = useState(''); const [deposit, setDeposit] = useState('0');
  const [depositReturned, setDepositReturned] = useState(false); const [recalculate, setRecalculate] = useState(false);
  const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [notice, setNotice] = useState('');
  const populate = (data: Rental) => {
    setRental(data); setStart(nepalDate(data.start_date)); setEnd(nepalDate(data.end_date));
    setPickupTime(nepalTime(data.start_date)); setReturnTime(nepalTime(data.end_date));
    setNotes(data.operations.notes); setDeposit(data.operations.deposit_amount); setDepositReturned(data.operations.deposit_returned); setRecalculate(false);
  };
  const load = useCallback(async () => {
    setBusy(true); setError('');
    try { populate((await api.get(`/bookings/${id}/`)).data); }
    catch (failure) { setError(errorMessage(failure)); }
    finally { setBusy(false); }
  }, [id]);
  useFocusEffect(useCallback(() => { void load(); }, [load]));
  const run = async (operation: () => Promise<void>) => {
    if (busy) return; setBusy(true); setError(''); setNotice('');
    try { await operation(); } catch (failure) { setError(errorMessage(failure)); } finally { setBusy(false); }
  };
  const mutate = async (path: string, values: object, patch = false) => {
    const response = patch ? await api.patch(path, values) : await api.post(path, values);
    populate(response.data); setNotice('Rental updated.'); void reminders.sync();
  };
  const closed = rental && ['completed', 'cancelled'].includes(rental.status);
  const datesChanged = !!rental && (start !== nepalDate(rental.start_date) || end !== nepalDate(rental.end_date) || pickupTime !== nepalTime(rental.start_date) || returnTime !== nepalTime(rental.end_date));
  return <Screen><Notice text={error} error /><Notice text={notice} />
    {!rental ? <Button title="Reload rental" busy={busy} onPress={() => void load()} /> : <>
      <View style={ui.row}><Text style={ui.eyebrow}>RENTAL #{rental.id}</Text><Badge state={rental.due_state} /></View>
      <Text style={ui.title}>{rental.bike_name}</Text>
      <View style={ui.card}><Text style={ui.heading}>{rental.customer_name || 'Customer'}</Text><Text style={ui.subtitle}>{rental.customer_phone || 'Phone not recorded'}</Text><Text style={ui.subtitle}>{rental.customer_email}</Text>
        <Text style={ui.subtitle}>Pickup: {displayDate(rental.start_date)}</Text><Text style={ui.subtitle}>Return: {displayDate(rental.end_date)} · Nepal time</Text>
        {rental.status === 'confirmed' && <Button title="Remind customer on WhatsApp" icon="logo-whatsapp" secondary busy={busy} disabled={datesChanged} onPress={() => void run(async () => { const { data } = await api.post(`/bookings/${id}/whatsapp-reminder/`); await Linking.openURL(data.url); })} />}
        {datesChanged && <Text style={ui.subtitle}>Save the new dates before preparing a customer reminder.</Text>}
      </View>
      <View style={ui.card}><Text style={ui.heading}>Rental balance</Text><Text style={ui.subtitle}>Agreed total: {money(rental.total_price)} · Received: {money(rental.paid_amount)}</Text><Text style={ui.heading}>{money(rental.balance_due)} outstanding</Text>
        {Number(rental.balance_due) > 0 && rental.status !== 'cancelled' && <Button title="Record full payment received" secondary busy={busy} onPress={() => void run(async () => { if (await confirmAction('Record payment?', `Confirm you received the remaining ${money(rental.balance_due)}. This records the payment; it does not charge the customer.`)) await mutate(`/bookings/${id}/mark-paid/`, { expected_updated_at: rental.updated_at }); })} />}
      </View>
      {!closed && <View style={ui.card}><Text style={ui.heading}>Dates & handover</Text><Text style={ui.subtitle}>All times below are Nepal time. The usual return deadline is 7 PM.</Text>
        <RentalDate label="Pickup date" value={start} onChange={setStart} /><Field label="Pickup time (HH:MM)" value={pickupTime} onChangeText={setPickupTime} maxLength={5} />
        <RentalDate label="Return date" value={end} onChange={setEnd} /><Field label="Return time (HH:MM)" value={returnTime} onChangeText={setReturnTime} maxLength={5} />
        <View style={ui.row}><Text style={[ui.subtitle, { flex: 1 }]}>Recalculate the agreed price for these dates</Text><Switch accessibilityLabel="Recalculate agreed price" value={recalculate} onValueChange={setRecalculate} /></View>
        <Field label="Security deposit (NPR)" value={deposit} onChangeText={setDeposit} keyboardType="decimal-pad" />
        <View style={ui.row}><Text style={ui.subtitle}>Deposit returned to customer</Text><Switch accessibilityLabel="Deposit returned" value={depositReturned} onValueChange={setDepositReturned} /></View>
        <Field label="Team notes" value={notes} onChangeText={setNotes} multiline maxLength={2000} />
        <Button title="Save changes" busy={busy} icon="save-outline" onPress={() => void run(async () => {
          const startDate = rentalDateTime(start, pickupTime), endDate = rentalDateTime(end, returnTime);
          if (Date.parse(endDate) <= Date.parse(startDate)) throw new Error('Return must be after pickup.');
          if (!Number.isFinite(Number(deposit)) || Number(deposit) < 0) throw new Error('Enter a valid deposit amount.');
          if (recalculate && !await confirmAction('Update the agreed price?', 'The duration-based price and outstanding balance will be recalculated. Existing payments will be kept.')) return;
          await mutate(`/bookings/${id}/`, { expected_updated_at: rental.updated_at, start_date: startDate, end_date: endDate, notes, deposit_amount: deposit, deposit_returned: depositReturned, recalculate_price: recalculate }, true);
        })} />
      </View>}
      {rental.status === 'pending' && <Button title="Confirm reservation" busy={busy} onPress={() => void run(async () => { await mutate(`/bookings/${id}/`, { expected_updated_at: rental.updated_at, status: 'confirmed' }, true); })} />}
      {rental.status === 'confirmed' && Date.parse(rental.start_date) <= Date.now() && <Button title="Record bike returned" busy={busy} icon="checkmark-circle-outline" onPress={() => void run(async () => { if (await confirmAction('Has the bike been returned?', 'Confirm the vehicle is physically back at the shop. Any outstanding balance stays recorded. Unsaved date changes will not be applied.')) await mutate(`/bookings/${id}/return/`, { expected_updated_at: rental.updated_at, notes, deposit_returned: depositReturned }); })} />}
      {!closed && (rental.status === 'pending' || Date.parse(rental.start_date) > Date.now()) && <Button title="Cancel reservation" secondary danger busy={busy} onPress={() => void run(async () => { if (await confirmAction('Cancel this reservation?', 'This releases its scheduled vehicle dates. No refund is issued automatically.')) await mutate(`/bookings/${id}/`, { expected_updated_at: rental.updated_at, status: 'cancelled' }, true); })} />}
      {rental.operations.returned_at && <Notice text={`Returned ${displayDate(rental.operations.returned_at)}. Deposit ${rental.operations.deposit_returned ? 'returned' : 'not marked returned'}.`} />}
      {rental.status === 'completed' && <View style={ui.card}><Text style={ui.heading}>Return handover</Text><Field label="Handover notes" value={notes} onChangeText={setNotes} multiline maxLength={2000} /><View style={ui.row}><Text style={ui.subtitle}>Deposit returned to customer</Text><Switch accessibilityLabel="Deposit returned after handover" value={depositReturned} onValueChange={setDepositReturned} /></View><Button title="Save handover notes" secondary busy={busy} onPress={() => void run(async () => { await mutate(`/bookings/${id}/`, { expected_updated_at: rental.updated_at, notes, deposit_returned: depositReturned }, true); })} /></View>}
      <View style={ui.card}><Text style={ui.heading}>Documents</Text><Button title="Download invoice" secondary busy={busy} onPress={() => void run(() => openRentalDocument(rental.id, 'invoice'))} /><Button title="Download rental agreement" secondary busy={busy} onPress={() => void run(() => openRentalDocument(rental.id, 'contract'))} /></View>
    </>}
  </Screen>;
}
