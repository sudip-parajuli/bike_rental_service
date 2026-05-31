import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  FlatList,
  Image,
  TouchableOpacity,
  TextInput,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialIcons } from '@expo/vector-icons';
import api, { BASE_MEDIA_URL } from '../../api';

export default function BikesScreen() {
  const [bikes, setBikes] = useState<any[]>([]);
  const [filtered, setFiltered] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const router = useRouter();

  useEffect(() => {
    fetchBikes();
  }, []);

  useEffect(() => {
    const q = search.toLowerCase();
    setFiltered(bikes.filter(b =>
      b.name?.toLowerCase().includes(q) ||
      b.brand?.toLowerCase().includes(q) ||
      b.vehicle_number?.toLowerCase().includes(q)
    ));
  }, [search, bikes]);

  const fetchBikes = async () => {
    try {
      const response = await api.get('/bikes/');
      const data = response.data?.results ?? response.data;
      setBikes(data);
      setFiltered(data);
    } catch (error) {
      console.log('Error fetching bikes:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const renderItem = ({ item }: { item: any }) => (
    <TouchableOpacity
      style={styles.bikeCard}
      onPress={() => router.push(`/bike/${item.id}`)}
      activeOpacity={0.85}
    >
      <Image
        source={{ uri: item.image?.startsWith('http') ? item.image : `${BASE_MEDIA_URL}${item.image}` }}
        style={styles.bikeImage}
        defaultSource={{ uri: 'https://placehold.co/120x120/006875/ffffff?text=Bike' }}
      />
      <View style={styles.bikeInfo}>
        <Text style={styles.bikeName}>{item.brand} {item.name}</Text>
        <View style={styles.specRow}>
          <Text style={styles.bikeDetails}>Year: {item.model_year || '—'}</Text>
          <Text style={styles.dividerDot}>•</Text>
          <Text style={styles.bikeDetails}>Plate: {item.vehicle_number || '—'}</Text>
        </View>
        <Text style={styles.rateText}>Rs. {item.price_per_day} / day</Text>
        <View style={[
          styles.statusBadge,
          { backgroundColor: item.availability_status ? '#dcfce7' : '#fee2e2' }
        ]}>
          <Text style={[
            styles.statusText,
            { color: item.availability_status ? '#166534' : '#991b1b' }
          ]}>
            ● {item.availability_status ? 'Available' : 'Rented'}
          </Text>
        </View>
      </View>
      <MaterialIcons name="chevron-right" size={24} color="#bac9cc" style={styles.arrowIcon} />
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#006875" />
      </View>
    );
  }

  return (
    <View style={styles.safeContainer}>
      {/* Title Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Bike Inventory</Text>
        <Text style={styles.headerSubtitle}>View and manage rental fleet status</Text>
      </View>

      {/* Search Input Bar */}
      <View style={styles.searchContainer}>
        <MaterialIcons name="search" size={20} color="#6b7a7d" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search by brand, name, plate..."
          placeholderTextColor="#94a3b8"
          value={search}
          onChangeText={setSearch}
        />
        {search.length > 0 && (
          <TouchableOpacity onPress={() => setSearch('')}>
            <MaterialIcons name="cancel" size={20} color="#6b7a7d" style={styles.clearIcon} />
          </TouchableOpacity>
        )}
      </View>

      {/* Flat List */}
      {filtered.length === 0 ? (
        <View style={styles.center}>
          <MaterialIcons name="two-wheeler" size={48} color="#bac9cc" />
          <Text style={styles.emptyText}>No bikes found.</Text>
        </View>
      ) : (
        <FlatList
          data={filtered}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderItem}
          contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchBikes(); }} colors={['#006875']} />
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  safeContainer: {
    flex: 1,
    backgroundColor: '#f3fbfc', // Clinical light theme background
  },
  center: { 
    flex: 1, 
    justifyContent: 'center', 
    alignItems: 'center',
    padding: 32
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 54,
    paddingBottom: 16,
    backgroundColor: '#ffffff',
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#006875',
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#6b7a7d',
    marginTop: 2,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    marginHorizontal: 16,
    marginTop: 16,
    marginBottom: 8,
    borderRadius: 8,
    paddingHorizontal: 12,
    height: 46,
    shadowColor: '#6b7a7d',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
  },
  searchIcon: { marginRight: 8 },
  searchInput: {
    flex: 1,
    fontSize: 13,
    color: '#1e293b',
    paddingVertical: 6,
  },
  clearIcon: { marginLeft: 8 },
  emptyText: { color: '#6b7a7d', fontSize: 15, marginTop: 12 },
  bikeCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    marginBottom: 12,
    flexDirection: 'row',
    overflow: 'hidden',
    shadowColor: '#6b7a7d',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 1,
    alignItems: 'center',
    paddingRight: 8,
  },
  bikeImage: { 
    width: 96, 
    height: 96,
    borderRadius: 8,
    margin: 8,
    backgroundColor: '#f3fbfc',
  },
  bikeInfo: { 
    paddingVertical: 8,
    paddingHorizontal: 4,
    flex: 1, 
    justifyContent: 'center' 
  },
  bikeName: { 
    fontSize: 15, 
    fontWeight: 'bold', 
    color: '#1e293b', 
    marginBottom: 4 
  },
  specRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  bikeDetails: { 
    fontSize: 11, 
    color: '#6b7a7d' 
  },
  dividerDot: {
    fontSize: 11,
    color: '#bac9cc',
    marginHorizontal: 6,
  },
  rateText: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#006875',
    marginBottom: 6,
  },
  statusBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  statusText: { 
    fontSize: 10, 
    fontWeight: 'bold' 
  },
  arrowIcon: { 
    marginRight: 4 
  },
});
