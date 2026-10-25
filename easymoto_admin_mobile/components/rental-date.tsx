import React, { useState } from 'react';
import { Platform, Pressable, Text, View } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { ui } from './staff-ui';

export function RentalDate({ label, value, onChange }: { label: string; value: string; onChange(value: string): void }) {
  const [open, setOpen] = useState(false);
  const local = new Date(`${value}T12:00:00`);
  return <View style={ui.field}><Text style={ui.label}>{label}</Text>
    {Platform.OS === 'web' ? React.createElement('input', { type: 'date', value, 'aria-label': label, onChange: (event: React.ChangeEvent<HTMLInputElement>) => onChange(event.target.value), style: { padding: 14, fontSize: 16, minHeight: 20, border: '1px solid #CFD8E5', borderRadius: 12, background: '#FFF', color: '#16263B', fontFamily: 'inherit' } }) : <>
      <Pressable accessibilityRole="button" accessibilityLabel={label} onPress={() => setOpen(true)} style={ui.input}><Text>{value}</Text></Pressable>
      {open && <DateTimePicker value={Number.isFinite(local.getTime()) ? local : new Date()} mode="date" onChange={(event, date) => {
        setOpen(Platform.OS === 'ios' && event.type !== 'dismissed');
        if (date) { onChange(`${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`); if (Platform.OS === 'ios') setOpen(false); }
      }} />}
    </>}
  </View>;
}
