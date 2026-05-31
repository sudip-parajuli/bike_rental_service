import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  FlatList,
  TouchableOpacity,
  Alert,
  Modal,
  RefreshControl,
  TextInput,
  Platform
} from 'react-native';
import { MaterialIcons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { openBrowserAsync } from 'expo-web-browser';
import api from '../../api';

const STATUS_COLORS: Record<string, string> = {
  confirmed: '#dcfce7',
  pending: '#fef9c3',
  cancelled: '#fee2e2',
  completed: '#e0f2fe',
};

const STATUS_TEXT_COLORS: Record<string, string> = {
  confirmed: '#166534',
  pending: '#854d0e',
  cancelled: '#991b1b',
  completed: '#075985',
};

export default function BookingsScreen() {
  const [bookings, setBookings] = useState<any[]>([]);
  const [filteredBookings, setFilteredBookings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedBooking, setSelectedBooking] = useState<any>(null);
  const [qrModalVisible, setQrModalVisible] = useState(false);
  const [customerModalVisible, setCustomerModalVisible] = useState(false);

  useEffect(() => {
    fetchBookings();
  }, []);

  useEffect(() => {
    const q = search.toLowerCase();
    if (!q) {
      setFilteredBookings(bookings);
    } else {
      setFilteredBookings(bookings.filter(b => 
        (b.bike_brand + ' ' + b.bike_name)?.toLowerCase().includes(q) ||
        b.customer_name?.toLowerCase().includes(q) ||
        b.customer_phone?.toLowerCase().includes(q) ||
        b.pickup_location?.toLowerCase().includes(q) ||
        b.status?.toLowerCase().includes(q) ||
        b.payment_status?.toLowerCase().includes(q)
      ));
    }
  }, [search, bookings]);

  const fetchBookings = async () => {
    try {
      const response = await api.get('/bookings/');
      const data = response.data?.results ?? response.data;
      const sortedData = Array.isArray(data) ? data : [];
      setBookings(sortedData);
      setFilteredBookings(sortedData);
    } catch (error) {
      console.log('Error fetching bookings:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleMarkPaid = async (bookingId: number) => {
    Alert.alert('Confirm Payment', 'Mark this booking as fully paid?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Confirm', 
        onPress: async () => {
          try {
            await api.post(`/bookings/${bookingId}/mark-paid/`);
            Alert.alert('Success', 'Booking marked as paid!');
            fetchBookings();
          } catch (error) {
            Alert.alert('Error', 'Could not mark as paid.');
          }
        }
      }
    ]);
  };

  const handleOpenInvoice = async (bookingId: number) => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const url = `${api.defaults.baseURL}/bookings/${bookingId}/invoice/?token=${token}`;
      if (Platform.OS === 'web') {
        window.open(url, '_blank');
      } else {
        await openBrowserAsync(url);
      }
    } catch (error) {
      console.log('Error opening invoice:', error);
      Alert.alert('Error', 'Failed to open invoice PDF.');
    }
  };

  const handleOpenContract = async (bookingId: number) => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const url = `${api.defaults.baseURL}/bookings/${bookingId}/contract/?token=${token}`;
      if (Platform.OS === 'web') {
        window.open(url, '_blank');
      } else {
        await openBrowserAsync(url);
      }
    } catch (error) {
      console.log('Error opening contract:', error);
      Alert.alert('Error', 'Failed to open agreement PDF.');
    }
  };

  const renderItem = ({ item }: { item: any }) => (
    <View style={styles.bookingCard}>
      <TouchableOpacity activeOpacity={0.7} onPress={() => { setSelectedBooking(item); setCustomerModalVisible(true); }}>
        <View style={styles.cardHeader}>
          <View style={{ flex: 1 }}>
            <Text style={styles.bikeName}>
              {item.bike_brand || ''} {item.bike_name || `Bike #${item.bike}`}
            </Text>
            <Text style={styles.bookingId}>Booking ID: #{item.id}</Text>
          </View>
          <View style={[styles.statusBadge, { backgroundColor: STATUS_COLORS[item.status] || '#f1f5f9' }]}>
            <Text style={[styles.statusBadgeText, { color: STATUS_TEXT_COLORS[item.status] || '#475569' }]}>
              {item.status?.toUpperCase()}
            </Text>
          </View>
        </View>

        <View style={styles.detailsContainer}>
        <View style={styles.detailRow}>
          <MaterialIcons name="person" size={16} color="#6b7a7d" style={styles.detailIcon} />
          <Text style={styles.bookingDetail}>
            {item.customer_name || 'Unknown'} — {item.customer_phone || 'N/A'}
          </Text>
        </View>

        <View style={styles.detailRow}>
          <MaterialIcons name="event" size={16} color="#6b7a7d" style={styles.detailIcon} />
          <Text style={styles.bookingDetail}>
            {new Date(item.start_date).toLocaleDateString()} → {new Date(item.end_date).toLocaleDateString()}
          </Text>
        </View>

        <View style={styles.detailRow}>
          <MaterialIcons name="place" size={16} color="#6b7a7d" style={styles.detailIcon} />
          <Text style={styles.bookingDetail}>{item.pickup_location}</Text>
        </View>

        <View style={styles.detailRow}>
          <MaterialIcons name="payments" size={16} color="#6b7a7d" style={styles.detailIcon} />
          <Text style={styles.bookingDetail}>Total Price: <Text style={{ fontWeight: 'bold', color: '#006875' }}>Rs. {item.total_price}</Text></Text>
        </View>
        </View>
      </TouchableOpacity>

      <View style={styles.paymentRow}>
        <View style={[
          styles.paymentBadge,
          { backgroundColor: item.payment_status === 'paid' ? '#dcfce7' : item.payment_status === 'partial' ? '#fef9c3' : '#fee2e2' }
        ]}>
          <Text style={[
            styles.paymentText,
            { color: item.payment_status === 'paid' ? '#166534' : item.payment_status === 'partial' ? '#854d0e' : '#991b1b' }
          ]}>
            ● Payment: {item.payment_status?.toUpperCase()}
          </Text>
        </View>
      </View>

      {item.payment_status !== 'paid' && item.status !== 'cancelled' && (
        <View style={styles.actionsRow}>
          <TouchableOpacity 
            style={styles.qrButton} 
            onPress={() => { setSelectedBooking(item); setQrModalVisible(true); }}
            activeOpacity={0.8}
          >
            <MaterialIcons name="qr-code" size={16} color="#ffffff" />
            <Text style={styles.actionText}>Show QR</Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.payButton} 
            onPress={() => handleMarkPaid(item.id)}
            activeOpacity={0.8}
          >
            <MaterialIcons name="check" size={16} color="#ffffff" />
            <Text style={styles.actionText}>Mark Paid</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
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
        <Text style={styles.headerTitle}>Rental Bookings</Text>
        <Text style={styles.headerSubtitle}>View and manage customer bookings</Text>
      </View>

      {/* Search Input Bar */}
      <View style={styles.searchContainer}>
        <MaterialIcons name="search" size={20} color="#6b7a7d" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search by customer, bike model, location..."
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

      {/* Bookings List */}
      {filteredBookings.length === 0 ? (
        <View style={styles.center}>
          <MaterialIcons name="book-online" size={48} color="#bac9cc" />
          <Text style={styles.emptyText}>No bookings found.</Text>
        </View>
      ) : (
        <FlatList
          data={filteredBookings}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderItem}
          contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchBookings(); }} colors={['#006875']} />
          }
        />
      )}

      {/* QR Modal */}
      <Modal animationType="slide" transparent visible={qrModalVisible} onRequestClose={() => setQrModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>eSewa / Fonepay QR</Text>
              <TouchableOpacity onPress={() => setQrModalVisible(false)}>
                <MaterialIcons name="close" size={24} color="#1e293b" />
              </TouchableOpacity>
            </View>

            <View style={styles.qrPlaceholder}>
              <Text style={styles.qrText}>📱</Text>
              <Text style={styles.qrSubText}>Scan using eSewa or Mobile Banking</Text>
              {selectedBooking && (
                <Text style={styles.qrAmount}>Rs. {selectedBooking.total_price}</Text>
              )}
            </View>
            <Text style={styles.qrHint}>Ask the customer to scan this QR code and complete their rental payment.</Text>
            
            <TouchableOpacity style={styles.closeButton} onPress={() => setQrModalVisible(false)}>
              <Text style={styles.closeButtonText}>Done</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Customer Details Modal */}
      <Modal animationType="fade" transparent visible={customerModalVisible} onRequestClose={() => setCustomerModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Customer Details</Text>
              <TouchableOpacity onPress={() => setCustomerModalVisible(false)}>
                <MaterialIcons name="close" size={24} color="#1e293b" />
              </TouchableOpacity>
            </View>

            {selectedBooking && (
              <View style={styles.customerDetailsContainer}>
                <View style={styles.customerDetailRow}>
                  <MaterialIcons name="person" size={20} color="#006875" />
                  <View style={styles.customerDetailTextContainer}>
                    <Text style={styles.customerDetailLabel}>Full Name</Text>
                    <Text style={styles.customerDetailValue}>{selectedBooking.customer_name || 'N/A'}</Text>
                  </View>
                </View>

                <View style={styles.customerDetailRow}>
                  <MaterialIcons name="phone" size={20} color="#006875" />
                  <View style={styles.customerDetailTextContainer}>
                    <Text style={styles.customerDetailLabel}>Phone Number</Text>
                    <Text style={styles.customerDetailValue}>{selectedBooking.customer_phone || 'N/A'}</Text>
                  </View>
                </View>

                <View style={styles.customerDetailRow}>
                  <MaterialIcons name="email" size={20} color="#006875" />
                  <View style={styles.customerDetailTextContainer}>
                    <Text style={styles.customerDetailLabel}>Email</Text>
                    <Text style={styles.customerDetailValue}>{selectedBooking.customer_email || 'N/A'}</Text>
                  </View>
                </View>

                <View style={styles.customerDetailRow}>
                  <MaterialIcons name="public" size={20} color="#006875" />
                  <View style={styles.customerDetailTextContainer}>
                    <Text style={styles.customerDetailLabel}>Nationality</Text>
                    <Text style={styles.customerDetailValue}>{selectedBooking.customer_nationality || 'N/A'}</Text>
                  </View>
                </View>

                <View style={styles.customerDetailRow}>
                  <MaterialIcons name="home" size={20} color="#006875" />
                  <View style={styles.customerDetailTextContainer}>
                    <Text style={styles.customerDetailLabel}>Address</Text>
                    <Text style={styles.customerDetailValue}>{selectedBooking.customer_address || 'N/A'}</Text>
                  </View>
                </View>
              </View>
            )}
            
            {selectedBooking && (
              <View style={styles.printButtonsRow}>
                <TouchableOpacity style={styles.printButton} onPress={() => handleOpenInvoice(selectedBooking.id)} activeOpacity={0.7}>
                  <MaterialIcons name="print" size={18} color="#006875" />
                  <Text style={styles.printButtonText}>Print Invoice</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.printButton} onPress={() => handleOpenContract(selectedBooking.id)} activeOpacity={0.7}>
                  <MaterialIcons name="description" size={18} color="#006875" />
                  <Text style={styles.printButtonText}>Print Contract</Text>
                </TouchableOpacity>
              </View>
            )}
            
            <TouchableOpacity style={styles.closeButton} onPress={() => setCustomerModalVisible(false)}>
              <Text style={styles.closeButtonText}>Close</Text>
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
  bookingCard: {
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
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 14,
  },
  bikeName: { 
    fontSize: 15, 
    fontWeight: 'bold', 
    color: '#1e293b', 
  },
  bookingId: {
    fontSize: 11,
    color: '#6b7a7d',
    marginTop: 2,
  },
  statusBadge: { 
    paddingHorizontal: 8, 
    paddingVertical: 3, 
    borderRadius: 6 
  },
  statusBadgeText: { 
    fontSize: 10, 
    fontWeight: 'bold' 
  },
  detailsContainer: {
    backgroundColor: '#f3fbfc',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  detailIcon: {
    marginRight: 8,
  },
  bookingDetail: { 
    fontSize: 12, 
    color: '#1e293b', 
  },
  paymentRow: { 
    marginBottom: 12 
  },
  paymentBadge: { 
    alignSelf: 'flex-start', 
    paddingHorizontal: 10, 
    paddingVertical: 4, 
    borderRadius: 6 
  },
  paymentText: { 
    fontSize: 11, 
    fontWeight: 'bold' 
  },
  actionsRow: { 
    flexDirection: 'row', 
    justifyContent: 'flex-end', 
    gap: 8, 
    marginTop: 4 
  },
  qrButton: { 
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#6b7a7d', 
    paddingHorizontal: 12, 
    paddingVertical: 8, 
    borderRadius: 6,
    gap: 4
  },
  payButton: { 
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#006875', 
    paddingHorizontal: 12, 
    paddingVertical: 8, 
    borderRadius: 6,
    gap: 4
  },
  actionText: { 
    color: '#ffffff', 
    fontWeight: 'bold', 
    fontSize: 12 
  },
  modalOverlay: { 
    flex: 1, 
    backgroundColor: 'rgba(0,0,0,0.5)', 
    justifyContent: 'center', 
    alignItems: 'center' 
  },
  modalContent: { 
    backgroundColor: '#ffffff', 
    padding: 24, 
    borderRadius: 16, 
    alignItems: 'center', 
    width: '85%' 
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: { 
    fontSize: 18, 
    fontWeight: 'bold', 
    color: '#1e293b' 
  },
  qrPlaceholder: { 
    width: 200, 
    height: 200, 
    backgroundColor: '#f3fbfc', 
    borderRadius: 12, 
    justifyContent: 'center', 
    alignItems: 'center', 
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#bac9cc',
    borderStyle: 'dashed'
  },
  qrText: { fontSize: 44 },
  qrSubText: { fontSize: 11, color: '#6b7a7d', marginTop: 8 },
  qrAmount: { fontSize: 20, fontWeight: 'bold', color: '#006875', marginTop: 6 },
  qrHint: { 
    fontSize: 12, 
    color: '#6b7a7d', 
    marginBottom: 20, 
    textAlign: 'center', 
    lineHeight: 18 
  },
  closeButton: { 
    backgroundColor: '#006875', 
    paddingHorizontal: 32, 
    paddingVertical: 12, 
    borderRadius: 8,
    width: '100%',
    alignItems: 'center'
  },
  closeButtonText: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  customerDetailsContainer: {
    width: '100%',
    marginBottom: 20,
  },
  customerDetailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  customerDetailTextContainer: {
    marginLeft: 12,
  },
  customerDetailLabel: {
    fontSize: 11,
    color: '#6b7a7d',
  },
  customerDetailValue: {
    fontSize: 14,
    color: '#1e293b',
    fontWeight: '500',
    marginTop: 2,
  },
  printButtonsRow: {
    flexDirection: 'row',
    gap: 12,
    marginVertical: 16,
    width: '100%',
  },
  printButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: '#006875',
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: '#ffffff',
    gap: 6,
  },
  printButtonText: {
    color: '#006875',
    fontWeight: 'bold',
    fontSize: 13,
  },
});
