import React, { useCallback, useEffect, useState } from 'react';
import { Switch, Text, View } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { router, useLocalSearchParams } from 'expo-router';
import api, { errorMessage } from '@/api';
import { Vehicle, listResults, money, nepalDate, rentalDateTime, estimateRentalPrice } from '@/lib/rentals';
import { useReminders } from '@/providers/reminders';
import { RentalDate } from '@/components/rental-date';
import { Button, Field, Notice, Screen, ui } from '@/components/staff-ui';

export default function CreateRental() {
  const { phone } = useLocalSearchParams<{ phone: string }>();
  const reminders = useReminders();
  const [vehicles, setVehicles] = useState<Vehicle[]>([]); const [bike, setBike] = useState('');
  const [start, setStart] = useState(nepalDate()); const [end, setEnd] = useState(nepalDate());
  const [pickupTime, setPickupTime] = useState('09:00');
  const [license, setLicense] = useState(''); const [identity, setIdentity] = useState('');
  const [deposit, setDeposit] = useState('5000'); const [advance, setAdvance] = useState('0'); const [discount, setDiscount] = useState('0');
  const [notes, setNotes] = useState(''); const [helmet, setHelmet] = useState(true); const [idp, setIdp] = useState(false);
  const [guarantorName, setGuarantorName] = useState(''); const [guarantorPhone, setGuarantorPhone] = useState(''); const [guarantorAddress, setGuarantorAddress] = useState('');
  const [bungy, setBungy] = useState(false); const [maps, setMaps] = useState(false);
  const [method, setMethod] = useState('cash'); const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      let page = 1; let more = true; const all: Vehicle[] = [];
      while (more && page <= 10) { const { data } = await api.get('/bikes/', { params: { page, page_size: 100 } }); all.push(...listResults<Vehicle>(data)); more = !!data.next; page++; }
      const available = all.filter(value => value.is_approved && value.availability_status);
      setVehicles(available); setBike(String(available[0]?.id || ''));
      if (phone) { const { data } = await api.get('/customers/walk-in/', { params: { phone } }); setLicense(data.driving_license_no || ''); setIdentity(data.passport_no || ''); }
    } catch (failure) { setError(errorMessage(failure)); } finally { setLoading(false); }
  }, [phone]);
  useEffect(() => { void load(); }, [load]);
  const selected = vehicles.find(value => String(value.id) === bike);
  const estimate = selected ? estimateRentalPrice(Number(selected.price_per_day), start, end, Number(discount)) : null;
  const create = async () => {
    if (!phone || !bike || !license.trim()) { setError('Select a customer and vehicle, and verify the driving licence.'); return; }
    setBusy(true); setError('');
    try {
      const startDate = rentalDateTime(start, pickupTime), endDate = rentalDateTime(end, '19:00');
      if (Date.parse(endDate) <= Date.parse(startDate)) throw new Error('Return must be after pickup. Select a later return date.');
      for (const value of [deposit, advance, discount]) if (!value.trim() || !Number.isFinite(Number(value)) || Number(value) < 0) throw new Error('Enter valid nonnegative amounts.');
      const { data } = await api.post('/bookings/walk-in/', { phone_number: phone, bike_id: Number(bike), start_date: startDate, end_date: endDate, driving_license_no: license, passport_no: identity, deposit_amount: deposit, advance_amount: advance, manual_discount: discount, payment_method: method, helmet, bungy_cord: bungy, maps, guarantor_name: guarantorName, guarantor_phone: guarantorPhone, guarantor_address: guarantorAddress, notes: [notes, idp ? 'International Driving Permit verified by staff.' : ''].filter(Boolean).join('\n') });
      void reminders.sync(); router.replace({ pathname: '/booking/[id]', params: { id: data.booking_id } });
    } catch (failure) { setError(errorMessage(failure)); } finally { setBusy(false); }
  };
  return <Screen><Text style={ui.eyebrow}>NEW RENTAL Â· STEP 2 OF 2</Text><Text style={ui.title}>Set up the ride.</Text><Text style={ui.subtitle}>Customer: {phone || 'Select a customer first'} Â· Times are Nepal time.</Text>
    <Notice text={error} error />
    <View style={ui.card}><Text style={ui.heading}>Vehicle & dates</Text>
      <Picker accessibilityLabel="Vehicle" selectedValue={bike} onValueChange={setBike}>{vehicles.map(value => <Picker.Item key={value.id} label={value.name + ' Â· ' + (value.vehicle_number || '')} value={String(value.id)} />)}</Picker>
      {selected && <Text style={ui.subtitle}>{money(selected.price_per_day)} per rental day. The server checks conflicts and calculates the agreed total when saved.</Text>}
      {!selected && !loading && <Notice text="No approved vehicles are ready. Check the fleet or refresh." />}
      <RentalDate label="Pickup date" value={start} onChange={setStart} /><Field label="Pickup time (HH:MM)" value={pickupTime} onChangeText={setPickupTime} maxLength={5} />
      <RentalDate label="Return date (7 PM)" value={end} onChange={setEnd} /><Text style={ui.subtitle}>Daily rentals, due by 7 PM. The NPR 500 late/night charge is discussed with the team; it is not charged automatically.</Text>
    </View>
    <View style={ui.card}><Text style={ui.heading}>Documents & equipment</Text><Field label="Driving licence number (verified)" value={license} onChangeText={setLicense} autoCapitalize="characters" /><Field label="Passport / citizenship / national ID" value={identity} onChangeText={setIdentity} />
      <View style={ui.row}><Text style={ui.subtitle}>Helmet supplied</Text><Switch accessibilityLabel="Helmet supplied" value={helmet} onValueChange={setHelmet} /></View>
      <View style={ui.row}><Text style={ui.subtitle}>Bungy cord supplied</Text><Switch accessibilityLabel="Bungy cord supplied" value={bungy} onValueChange={setBungy} /></View>
      <View style={ui.row}><Text style={ui.subtitle}>Maps supplied</Text><Switch accessibilityLabel="Maps supplied" value={maps} onValueChange={setMaps} /></View>
      <View style={ui.row}><Text style={[ui.subtitle, { flex: 1 }]}>IDP verified (international rider)</Text><Switch accessibilityLabel="IDP verified" value={idp} onValueChange={setIdp} /></View>
    </View>
    <View style={ui.card}><Text style={ui.heading}>Accommodation / guarantor</Text><Text style={ui.subtitle}>Record the Nepal contact where required for an international rider.</Text><Field label="Guarantor or accommodation name" value={guarantorName} onChangeText={setGuarantorName} /><Field label="Guarantor phone" value={guarantorPhone} onChangeText={setGuarantorPhone} keyboardType="phone-pad" /><Field label="Guarantor / accommodation address" value={guarantorAddress} onChangeText={setGuarantorAddress} /></View>
    <View style={ui.card}><Text style={ui.heading}>Payment & security deposit</Text><Field label="Security deposit held (NPR)" value={deposit} onChangeText={setDeposit} keyboardType="decimal-pad" /><Field label="Rental payment received now (NPR)" value={advance} onChangeText={setAdvance} keyboardType="decimal-pad" /><Field label="Additional agreed discount (NPR)" value={discount} onChangeText={setDiscount} keyboardType="decimal-pad" />
      <Picker accessibilityLabel="Payment method" selectedValue={method} onValueChange={setMethod}><Picker.Item label="Cash received" value="cash" /><Picker.Item label="QR payment verified by staff" value="qr" /></Picker>
      <Text style={ui.subtitle}>The deposit is recorded separately from rental income. Only enter money actually received.</Text>
      <Field label="Team notes" value={notes} onChangeText={setNotes} multiline maxLength={1800} />
    </View>
    {estimate && <View style={ui.card}><Text style={ui.heading}>Estimated rental total: {money(estimate.total)}</Text><Text style={ui.subtitle}>{estimate.days} rental day(s) · Duration discount: {money(estimate.autoDiscount)}. Security deposit is separate. The final quote is validated when saved.</Text></View>}
    <Button title="Create confirmed rental" icon="checkmark-circle-outline" busy={busy || loading} disabled={!selected || !phone || !estimate} onPress={() => void create()} />
    <Button title="Refresh vehicle list" secondary onPress={() => void load()} busy={loading} />
  </Screen>;
}
