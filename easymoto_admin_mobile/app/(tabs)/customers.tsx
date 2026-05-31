import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  FlatList,
  TouchableOpacity,
  TextInput,
  Modal,
  RefreshControl,
  ScrollView,
  Platform
} from 'react-native';
import { MaterialIcons } from '@expo/vector-icons';
import api from '../../api';
import { useRouter } from 'expo-router';

export default function CustomersScreen() {
  const router = useRouter();
  const [customers, setCustomers] = useState<any[]>([]);
  const [filteredCustomers, setFilteredCustomers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  
  const [selectedCustomer, setSelectedCustomer] = useState<any>(null);
  const [detailsModalVisible, setDetailsModalVisible] = useState(false);

  useEffect(() => {
    fetchCustomers();
  }, []);

  useEffect(() => {
    const q = search.toLowerCase();
    if (!q) {
      setFilteredCustomers(customers);
    } else {
      setFilteredCustomers(customers.filter(c => 
        c.full_name?.toLowerCase().includes(q) ||
        c.phone_number?.toLowerCase().includes(q) ||
        c.email?.toLowerCase().includes(q) ||
        c.nationality?.toLowerCase().includes(q)
      ));
    }
  }, [search, customers]);

  const fetchCustomers = async () => {
    try {
      const response = await api.get('/customers/');
      const data = response.data?.results ?? response.data;
      const sortedData = Array.isArray(data) ? data : [];
      setCustomers(sortedData);
      setFilteredCustomers(sortedData);
    } catch (error) {
      console.log('Error fetching customers:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'confirmed': return { bg: '#dcfce7', text: '#166534' };
      case 'pending': return { bg: '#fef9c3', text: '#854d0e' };
      case 'cancelled': return { bg: '#fee2e2', text: '#991b1b' };
      case 'completed': return { bg: '#e0f2fe', text: '#075985' };
      default: return { bg: '#f1f5f9', text: '#475569' };
    }
  };

  const renderCustomerItem = ({ item }: { item: any }) => (
    <TouchableOpacity 
      style={styles.customerCard}
      activeOpacity={0.7}
      onPress={() => { setSelectedCustomer(item); setDetailsModalVisible(true); }}
    >
      <View style={styles.cardHeader}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {(item.full_name || 'U').charAt(0).toUpperCase()}
          </Text>
        </View>
        <View style={styles.headerInfo}>
          <Text style={styles.customerName}>{item.full_name || 'Unknown User'}</Text>
          <Text style={styles.customerUsername}>@{item.username || 'username'}</Text>
        </View>
        <View style={styles.badgeContainer}>
          <View style={styles.bookingBadge}>
            <Text style={styles.bookingBadgeText}>
              {item.booking_count || 0} {item.booking_count === 1 ? 'Booking' : 'Bookings'}
            </Text>
          </View>
        </View>
      </View>

      <View style={styles.contactDetails}>
        <View style={styles.contactRow}>
          <MaterialIcons name="phone" size={14} color="#6b7a7d" style={styles.contactIcon} />
          <Text style={styles.contactText}>{item.phone_number || 'No phone number'}</Text>
        </View>
        {item.email ? (
          <View style={styles.contactRow}>
            <MaterialIcons name="email" size={14} color="#6b7a7d" style={styles.contactIcon} />
            <Text style={styles.contactText} numberOfLines={1}>{item.email}</Text>
          </View>
        ) : null}
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.safeContainer}>
      {/* Title Header */}
      <View style={styles.header}>
        <View style={styles.headerMain}>
          <View>
            <Text style={styles.headerTitle}>Customers</Text>
            <Text style={styles.headerSubtitle}>View registered customers and booking history</Text>
          </View>
          <TouchableOpacity 
            style={styles.addButton}
            onPress={() => router.push('/create-customer')}
            activeOpacity={0.8}
          >
            <MaterialIcons name="person-add" size={20} color="#ffffff" />
            <Text style={styles.addButtonText}>Add Walk-in</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Search Input Bar */}
      <View style={styles.searchContainer}>
        <MaterialIcons name="search" size={20} color="#6b7a7d" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search by name, phone, email..."
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

      {/* Customers List */}
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#006875" />
        </View>
      ) : filteredCustomers.length === 0 ? (
        <View style={styles.center}>
          <MaterialIcons name="people" size={48} color="#bac9cc" />
          <Text style={styles.emptyText}>No customers found.</Text>
        </View>
      ) : (
        <FlatList
          data={filteredCustomers}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderCustomerItem}
          contentContainerStyle={{ padding: 16, paddingBottom: 80 }}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchCustomers(); }} colors={['#006875']} />
          }
        />
      )}

      {/* Details & History Modal */}
      <Modal animationType="slide" transparent visible={detailsModalVisible} onRequestClose={() => setDetailsModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Customer Profile</Text>
              <TouchableOpacity onPress={() => setDetailsModalVisible(false)}>
                <MaterialIcons name="close" size={24} color="#1e293b" />
              </TouchableOpacity>
            </View>

            {selectedCustomer && (
              <ScrollView style={styles.modalScroll} showsVerticalScrollIndicator={false}>
                {/* Profile Overview */}
                <View style={styles.profileHeader}>
                  <View style={styles.largeAvatar}>
                    <Text style={styles.largeAvatarText}>
                      {(selectedCustomer.full_name || 'U').charAt(0).toUpperCase()}
                    </Text>
                  </View>
                  <Text style={styles.modalCustomerName}>{selectedCustomer.full_name || 'Unknown User'}</Text>
                  <Text style={styles.modalCustomerUsername}>@{selectedCustomer.username}</Text>
                </View>

                {/* Details Section */}
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>Contact & Info</Text>
                  <View style={styles.infoCard}>
                    <View style={styles.infoRow}>
                      <MaterialIcons name="phone" size={18} color="#006875" />
                      <Text style={styles.infoValue}>{selectedCustomer.phone_number || 'N/A'}</Text>
                    </View>
                    <View style={styles.infoRow}>
                      <MaterialIcons name="email" size={18} color="#006875" />
                      <Text style={styles.infoValue}>{selectedCustomer.email || 'N/A'}</Text>
                    </View>
                    <View style={styles.infoRow}>
                      <MaterialIcons name="public" size={18} color="#006875" />
                      <Text style={styles.infoValue}>Nationality: {selectedCustomer.nationality || 'Nepali'}</Text>
                    </View>
                    <View style={styles.infoRow}>
                      <MaterialIcons name="home" size={18} color="#006875" />
                      <Text style={styles.infoValue} numberOfLines={2}>Address: {selectedCustomer.address || 'N/A'}</Text>
                    </View>
                  </View>
                </View>

                {/* Booking History Section */}
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>Booking History ({selectedCustomer.booking_count || 0})</Text>
                  {(!selectedCustomer.bookings || selectedCustomer.bookings.length === 0) ? (
                    <Text style={styles.noHistoryText}>No booking history found for this customer.</Text>
                  ) : (
                    selectedCustomer.bookings.map((booking: any) => {
                      const colors = getStatusColor(booking.status);
                      return (
                        <View key={booking.id} style={styles.historyCard}>
                          <View style={styles.historyHeader}>
                            <Text style={styles.historyBikeName}>
                              {booking.bike_brand} {booking.bike_name}
                            </Text>
                            <View style={[styles.historyStatusBadge, { backgroundColor: colors.bg }]}>
                              <Text style={[styles.historyStatusText, { color: colors.text }]}>
                                {booking.status?.toUpperCase()}
                              </Text>
                            </View>
                          </View>
                          
                          <View style={styles.historyDetails}>
                            <Text style={styles.historyDateText}>
                              {new Date(booking.start_date).toLocaleDateString()} → {new Date(booking.end_date).toLocaleDateString()}
                            </Text>
                            <View style={styles.historyPriceRow}>
                              <Text style={styles.historyPrice}>Rs. {booking.total_price}</Text>
                              <Text style={styles.historyPayment}>
                                Payment: {booking.payment_status?.toUpperCase()}
                              </Text>
                            </View>
                          </View>
                        </View>
                      );
                    })
                  )}
                </View>
              </ScrollView>
            )}

            <TouchableOpacity style={styles.closeButton} onPress={() => setDetailsModalVisible(false)}>
              <Text style={styles.closeButtonText}>Done</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  safeContainer: {
    flex: 1,
    backgroundColor: '#f3fbfc',
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
  headerMain: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#006875',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    gap: 4,
  },
  addButtonText: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: 12,
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
  customerCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#6b7a7d',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 1,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#e0f2fe',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#075985',
  },
  headerInfo: {
    flex: 1,
    marginLeft: 12,
  },
  customerName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  customerUsername: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 1,
  },
  badgeContainer: {
    justifyContent: 'center',
  },
  bookingBadge: {
    backgroundColor: '#f0fdfa',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 0.5,
    borderColor: '#ccfbf1',
  },
  bookingBadgeText: {
    fontSize: 11,
    color: '#0d9488',
    fontWeight: '600',
  },
  contactDetails: {
    borderTopWidth: 1,
    borderTopColor: '#f1f5f9',
    paddingTop: 10,
    gap: 6,
  },
  contactRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  contactIcon: {
    marginRight: 6,
  },
  contactText: {
    fontSize: 13,
    color: '#475569',
  },
  modalOverlay: { 
    flex: 1, 
    backgroundColor: 'rgba(0,0,0,0.5)', 
    justifyContent: 'flex-end'
  },
  modalContent: { 
    backgroundColor: '#ffffff', 
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    maxHeight: '90%',
    width: '100%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: { 
    fontSize: 20, 
    fontWeight: 'bold', 
    color: '#1e293b' 
  },
  modalScroll: {
    marginBottom: 20,
  },
  profileHeader: {
    alignItems: 'center',
    marginBottom: 24,
  },
  largeAvatar: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#e0f2fe',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
    borderWidth: 2,
    borderColor: '#bae6fd',
  },
  largeAvatarText: {
    fontSize: 30,
    fontWeight: 'bold',
    color: '#075985',
  },
  modalCustomerName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  modalCustomerUsername: {
    fontSize: 14,
    color: '#64748b',
    marginTop: 2,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#475569',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  infoCard: {
    backgroundColor: '#f3fbfc',
    borderRadius: 12,
    padding: 16,
    gap: 12,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  infoValue: {
    fontSize: 14,
    color: '#1e293b',
    flex: 1,
  },
  noHistoryText: {
    fontSize: 14,
    color: '#64748b',
    textAlign: 'center',
    marginVertical: 12,
    fontStyle: 'italic',
  },
  historyCard: {
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
  },
  historyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  historyBikeName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  historyStatusBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  historyStatusText: {
    fontSize: 10,
    fontWeight: 'bold',
  },
  historyDetails: {
    flexDirection: 'column',
    gap: 4,
  },
  historyDateText: {
    fontSize: 12,
    color: '#64748b',
  },
  historyPriceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
  },
  historyPrice: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#006875',
  },
  historyPayment: {
    fontSize: 11,
    fontWeight: '600',
    color: '#475569',
  },
  closeButton: { 
    backgroundColor: '#006875', 
    paddingVertical: 14, 
    borderRadius: 10,
    width: '100%',
    alignItems: 'center'
  },
  closeButtonText: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: 15,
  }
});
