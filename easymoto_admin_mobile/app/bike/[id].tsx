import React, { useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, ActivityIndicator, ScrollView,
  Image, TouchableOpacity, RefreshControl,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../../api';
 
export default function BikeDetailScreen() {
  const { id } = useLocalSearchParams();
  const router = useRouter();
  const [bike, setBike] = useState<any>(null);
  const [bookings, setBookings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isSuperuser, setIsSuperuser] = useState(false);
 
  const fetchData = async () => {
    try {
      const [bikeRes, bookingsRes] = await Promise.all([
        api.get(`/bikes/${id}/`),
        api.get(`/bikes/${id}/bookings/`),
      ]);
      setBike(bikeRes.data);
      const bData = bookingsRes.data?.results ?? bookingsRes.data;
      setBookings(Array.isArray(bData) ? bData : []);
    } catch (error) {
      console.log('Error fetching bike details:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };
 
  useEffect(() => {
    const checkRole = async () => {
      const superuserVal = await AsyncStorage.getItem('is_superuser');
      setIsSuperuser(superuserVal === 'true');
    };
    checkRole();
    fetchData();
  }, [id]);

  if (loading) return <View style={s.center}><ActivityIndicator size="large" color="#3b82f6" /></View>;
  if (!bike) return <View style={s.center}><Text>Bike not found</Text></View>;

  const imageUri = bike.image?.startsWith('http')
    ? bike.image
    : `http://localhost:8000${bike.image}`;

  const nextMaint = bike.next_maintenance_date;
  const isOverdue = nextMaint && new Date(nextMaint) < new Date();

  return (
    <ScrollView
      style={s.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchData(); }} />}
    >
      {/* Hero Image */}
      <Image source={{ uri: imageUri }} style={s.image} />

      {/* Basic Info */}
      <View style={s.section}>
        <Text style={s.title}>{bike.brand} {bike.name}</Text>
        <Text style={s.subtitle}>{bike.model_year} · {bike.type} · {bike.color || '—'}</Text>
        <Text style={s.price}>Rs. {bike.price_per_day} / day</Text>
        <View style={[s.badge, { backgroundColor: bike.availability_status ? '#dcfce7' : '#fee2e2' }]}>
          <Text style={[s.badgeText, { color: bike.availability_status ? '#166534' : '#991b1b' }]}>
            {bike.availability_status ? '● Available' : '● Rented Out'}
          </Text>
        </View>
        {bike.vehicle_number && <Text style={s.meta}>Plate: {bike.vehicle_number}</Text>}
        {bike.engine_type && <Text style={s.meta}>Engine: {bike.engine_type} · {bike.displacement}</Text>}
      </View>

      {/* Stats */}
      <View style={s.section}>
        <Text style={s.sectionTitle}>{isSuperuser ? 'Financial & Maintenance Overview' : 'Maintenance Status'}</Text>
        <View style={s.statsGrid}>
          {isSuperuser && (
            <>
              <StatBox label="Total Revenue" value={`Rs. ${bike.total_earnings || 0}`} color="#3b82f6" />
              <StatBox label="Maint. Cost" value={`Rs. ${bike.total_maintenance_cost || 0}`} color="#f59e0b" />
            </>
          )}
          <StatBox label="Maint. Count" value={String(bike.maintenance_count || 0)} color="#8b5cf6" />
          <StatBox
            label="Next Maint."
            value={nextMaint || 'Not set'}
            color={isOverdue ? '#ef4444' : '#10b981'}
          />
        </View>
        {isOverdue && (
          <View style={s.alertBox}>
            <Text style={s.alertText}>⚠️ Maintenance is overdue! Please service this bike immediately.</Text>
          </View>
        )}
      </View>

      {/* Maintenance History */}
      <View style={s.section}>
        <View style={s.rowBetween}>
          <Text style={s.sectionTitle}>Maintenance History</Text>
          <TouchableOpacity
            style={s.addBtn}
            onPress={() => router.push({ pathname: '/bike/add-maintenance', params: { bikeId: bike.id } })}
          >
            <Text style={s.addBtnText}>+ Add Record</Text>
          </TouchableOpacity>
        </View>
        {bike.maintenance_records?.length > 0 ? (
          bike.maintenance_records.map((r: any) => (
            <View key={r.id} style={s.recordCard}>
              <View style={s.rowBetween}>
                <Text style={s.recordTitle}>{r.date}</Text>
                <Text style={s.recordCost}>Rs. {r.cost}</Text>
              </View>
              <Text style={s.recordDesc}>{r.description}</Text>
            </View>
          ))
        ) : (
          <Text style={s.emptyText}>No maintenance records yet.</Text>
        )}
      </View>

      {/* Booking History */}
      <View style={s.section}>
        <Text style={s.sectionTitle}>Booking History ({bookings.length})</Text>
        {bookings.length > 0 ? (
          bookings.map((b: any) => (
            <View key={b.id} style={s.recordCard}>
              <View style={s.rowBetween}>
                <Text style={s.recordTitle}>Booking #{b.id}</Text>
                <View style={[s.statusPill, {
                  backgroundColor: b.status === 'confirmed' ? '#dcfce7' :
                    b.status === 'completed' ? '#e0f2fe' :
                    b.status === 'cancelled' ? '#fee2e2' : '#fef9c3'
                }]}>
                  <Text style={s.statusPillText}>{b.status}</Text>
                </View>
              </View>
              <Text style={s.recordDesc}>
                👤 {b.customer_name || 'Unknown'} · {b.customer_phone || ''}
              </Text>
              <Text style={s.recordDesc}>
                📅 {new Date(b.start_date).toLocaleDateString()} → {new Date(b.end_date).toLocaleDateString()}
              </Text>
              <Text style={s.recordDesc}>💰 Rs. {b.total_price} · Payment: {b.payment_status}</Text>
            </View>
          ))
        ) : (
          <Text style={s.emptyText}>No booking history.</Text>
        )}
      </View>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

function StatBox({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <View style={[s.statBox, { borderTopColor: color }]}>
      <Text style={s.statLabel}>{label}</Text>
      <Text style={[s.statValue, { color }]}>{value}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  container: { flex: 1, backgroundColor: '#f8fafc' },
  image: { width: '100%', height: 240 },
  section: { backgroundColor: '#fff', marginTop: 10, padding: 16 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#1e293b' },
  subtitle: { fontSize: 14, color: '#64748b', marginTop: 4 },
  price: { fontSize: 20, fontWeight: 'bold', color: '#3b82f6', marginTop: 8 },
  badge: { alignSelf: 'flex-start', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12, marginTop: 10 },
  badgeText: { fontWeight: '700', fontSize: 13 },
  meta: { fontSize: 13, color: '#64748b', marginTop: 6 },
  sectionTitle: { fontSize: 17, fontWeight: 'bold', color: '#1e293b', marginBottom: 12 },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  statBox: {
    width: '47%',
    backgroundColor: '#f8fafc',
    padding: 14,
    borderRadius: 10,
    borderTopWidth: 3,
  },
  statLabel: { fontSize: 12, color: '#64748b', marginBottom: 4 },
  statValue: { fontSize: 16, fontWeight: 'bold' },
  alertBox: { marginTop: 10, backgroundColor: '#fef2f2', borderRadius: 8, padding: 12, borderLeftWidth: 4, borderLeftColor: '#ef4444' },
  alertText: { color: '#991b1b', fontSize: 13 },
  addBtn: { backgroundColor: '#3b82f6', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 },
  addBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 13 },
  recordCard: { backgroundColor: '#f8fafc', borderRadius: 8, padding: 12, marginBottom: 8, borderWidth: 1, borderColor: '#e2e8f0' },
  recordTitle: { fontWeight: 'bold', color: '#334155', fontSize: 14 },
  recordCost: { fontWeight: 'bold', color: '#10b981', fontSize: 14 },
  recordDesc: { fontSize: 13, color: '#475569', marginTop: 4 },
  statusPill: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 10 },
  statusPillText: { fontSize: 11, fontWeight: '700', color: '#334155' },
  emptyText: { color: '#94a3b8', fontStyle: 'italic', fontSize: 14 },
});
