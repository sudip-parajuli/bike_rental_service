import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  TextInput,
  Modal,
  Linking,
  Dimensions
} from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialIcons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../../api';

const { width } = Dimensions.get('window');

export default function DashboardScreen() {
  const [stats, setStats] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]); // Maintenance alerts
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const [alertModalVisible, setAlertModalVisible] = useState(false);
  const [isSuperuser, setIsSuperuser] = useState(false);
  const [displayName, setDisplayName] = useState('Admin');
  const router = useRouter();

  const fetchDashboardData = async () => {
    try {
      const [statsRes, alertsRes] = await Promise.all([
        api.get('/dashboard/'),
        api.get('/alerts/maintenance/')
      ]);
      setStats(statsRes.data);
      setAlerts(alertsRes.data || []);
    } catch (error) {
      console.log('Error fetching stats:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    const init = async () => {
      const superuserVal = await AsyncStorage.getItem('is_superuser');
      const nameVal = await AsyncStorage.getItem('full_name') || await AsyncStorage.getItem('username') || 'Admin';
      setIsSuperuser(superuserVal === 'true');
      setDisplayName(nameVal);
      fetchDashboardData();
    };
    init();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchDashboardData();
  };

  const handleCall = (phoneNumber: string) => {
    if (!phoneNumber) return;
    Linking.openURL(`tel:${phoneNumber}`).catch(() => {
      alert('Failed to open phone call app.');
    });
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#006875" />
      </View>
    );
  }

  // Filter active rented bikes
  const rentedBikes = stats?.rented_bikes || [];
  const filteredRentals = rentedBikes.filter((rental: any) => {
    const q = search.toLowerCase();
    return (
      rental.bike_name?.toLowerCase().includes(q) ||
      rental.vehicle_number?.toLowerCase().includes(q) ||
      rental.customer_name?.toLowerCase().includes(q) ||
      rental.customer_phone?.toLowerCase().includes(q)
    );
  });

  const endingTodayCount = stats?.rental_end_alerts?.length || 0;
  const maintenanceCount = alerts.length || 0;
  const staffActivityCount = isSuperuser ? (stats?.staff_activity_notifications?.length || 0) : 0;
  const totalNotifications = endingTodayCount + maintenanceCount + staffActivityCount;

  const handleMarkStaffNotificationsRead = async () => {
    try {
      await api.post('/staff-activity/mark-read/');
      // Refetch to clear the badge
      fetchDashboardData();
    } catch (e) {
      console.log('Error marking read:', e);
    }
  };

  return (
    <View style={styles.safeContainer}>
      {/* Top Custom Header */}
      <View style={styles.customHeader}>
        <View>
          <Text style={styles.greetingText}>Namaste, {displayName}! 👋</Text>
          <Text style={styles.brandTitle}>EasyMoto Hub</Text>
        </View>
        <TouchableOpacity 
          style={styles.notificationBell}
          onPress={() => setAlertModalVisible(true)}
          activeOpacity={0.7}
        >
          <MaterialIcons name="notifications" size={28} color="#006875" />
          {totalNotifications > 0 && (
            <View style={styles.notificationBadge}>
              <Text style={styles.badgeText}>{totalNotifications}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      <ScrollView 
        style={styles.container}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#006875']} />
        }
      >
        {/* Morning Alert Warning Banner */}
        {endingTodayCount > 0 && (
          <TouchableOpacity 
            style={styles.warningBanner} 
            activeOpacity={0.9}
            onPress={() => setAlertModalVisible(true)}
          >
            <MaterialIcons name="warning" size={20} color="#991b1b" />
            <Text style={styles.warningText}>
              Morning Alert: {endingTodayCount} active rental{endingTodayCount > 1 ? 's are' : ' is'} ending today.
            </Text>
          </TouchableOpacity>
        )}

        {/* Global Search Bar */}
        <View style={styles.searchContainer}>
          <MaterialIcons name="search" size={20} color="#6b7a7d" style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search rented bikes, customers, plate..."
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

        {/* Horizontal Navigation Actions */}
        <Text style={styles.sectionHeader}>Quick Navigation</Text>
        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false} 
          style={styles.actionsBar}
          contentContainerStyle={{ paddingRight: 24 }}
        >
          <TouchableOpacity 
            style={styles.actionChip}
            onPress={() => router.push('/(tabs)/bikes')}
            activeOpacity={0.8}
          >
            <View style={[styles.actionIconContainer, { backgroundColor: '#e0f2fe' }]}>
              <MaterialIcons name="two-wheeler" size={22} color="#0284c7" />
            </View>
            <Text style={styles.actionLabel}>Bikes</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.actionChip}
            onPress={() => router.push('/(tabs)/bookings')}
            activeOpacity={0.8}
          >
            <View style={[styles.actionIconContainer, { backgroundColor: '#dcfce7' }]}>
              <MaterialIcons name="book-online" size={22} color="#16a34a" />
            </View>
            <Text style={styles.actionLabel}>Bookings</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.actionChip}
            onPress={() => router.push('/(tabs)/customers')}
            activeOpacity={0.8}
          >
            <View style={[styles.actionIconContainer, { backgroundColor: '#fef9c3' }]}>
              <MaterialIcons name="person-add" size={22} color="#ca8a04" />
            </View>
            <Text style={styles.actionLabel}>Walk-in</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.actionChip}
            onPress={() => setAlertModalVisible(true)}
            activeOpacity={0.8}
          >
            <View style={[styles.actionIconContainer, { backgroundColor: '#fee2e2' }]}>
              <MaterialIcons name="notifications-active" size={22} color="#dc2626" />
            </View>
            <Text style={styles.actionLabel}>Alert Center</Text>
          </TouchableOpacity>
        </ScrollView>

        {/* Financial Business HUD Panel — Admin only */}
        {isSuperuser && (
          <>
            <Text style={styles.sectionHeader}>Financial Overview</Text>
            <View style={styles.financialHud}>
              <View style={styles.profitHeaderRow}>
                <Text style={styles.profitLabel}>Net Cash Flow</Text>
                <View style={styles.profitBadge}>
                  <Text style={styles.profitBadgeText}>Live Stats</Text>
                </View>
              </View>
              <Text style={styles.netProfitValue}>Rs. {stats?.net_profit?.toLocaleString() || '0.00'}</Text>

              <View style={styles.hudDividingLine} />

              <View style={styles.financialRow}>
                <View style={styles.financialCol}>
                  <View style={styles.kpiIndicatorRow}>
                    <View style={[styles.dot, { backgroundColor: '#10b981' }]} />
                    <Text style={styles.kpiLabel}>Total Revenue</Text>
                  </View>
                  <Text style={[styles.kpiValue, { color: '#166534' }]}>
                    Rs. {stats?.total_revenue?.toLocaleString() || '0.00'}
                  </Text>
                </View>

                <View style={styles.financialVerticalDivider} />

                <View style={styles.financialCol}>
                  <View style={styles.kpiIndicatorRow}>
                    <View style={[styles.dot, { backgroundColor: '#ef4444' }]} />
                    <Text style={styles.kpiLabel}>Expenditures</Text>
                  </View>
                  <Text style={[styles.kpiValue, { color: '#991b1b' }]}>
                    Rs. {stats?.total_expenditure?.toLocaleString() || '0.00'}
                  </Text>
                </View>
              </View>
            </View>
          </>
        )}

        {/* Core Inventory Stats Cards */}
        <View style={styles.grid}>
          <View style={styles.smallCard}>
            <MaterialIcons name="check-circle" size={22} color="#006875" />
            <Text style={styles.smallCardValue}>{stats?.available_bikes || 0}</Text>
            <Text style={styles.smallCardTitle}>Available Bikes</Text>
          </View>

          <View style={styles.smallCard}>
            <MaterialIcons name="grid-view" size={22} color="#006875" />
            <Text style={styles.smallCardValue}>{stats?.total_bikes || 0}</Text>
            <Text style={styles.smallCardTitle}>Total Inventory</Text>
          </View>

          <View style={styles.smallCard}>
            <MaterialIcons name="input" size={22} color="#0284c7" />
            <Text style={styles.smallCardValue}>{stats?.today_pickups || 0}</Text>
            <Text style={styles.smallCardTitle}>Today Pickups</Text>
          </View>

          <View style={styles.smallCard}>
            <MaterialIcons name="call-received" size={22} color="#16a34a" />
            <Text style={styles.smallCardValue}>{stats?.today_returns || 0}</Text>
            <Text style={styles.smallCardTitle}>Today Returns</Text>
          </View>
        </View>

        {/* Currently Rented Bikes Section */}
        <View style={styles.rentedSectionTitleRow}>
          <Text style={styles.sectionHeaderRented}>Currently Rented Bikes</Text>
          <View style={styles.rentedCountBadge}>
            <Text style={styles.rentedCountText}>{rentedBikes.length} Active</Text>
          </View>
        </View>

        {filteredRentals.length === 0 ? (
          <View style={styles.emptyRentalsCard}>
            <MaterialIcons name="directions-bike" size={40} color="#bac9cc" />
            <Text style={styles.emptyRentalsText}>
              {search.length > 0 ? "No active rentals match your search." : "No bikes are currently on active rent."}
            </Text>
          </View>
        ) : (
          filteredRentals.map((rental: any) => {
            const isEndingToday = stats?.rental_end_alerts?.some((alert: any) => alert.booking_id === rental.booking_id);
            return (
              <View 
                key={rental.booking_id} 
                style={[
                  styles.rentalCard,
                  isEndingToday && { borderLeftColor: '#ef4444', borderLeftWidth: 4 }
                ]}
              >
                <View style={styles.rentalCardHeader}>
                  <View>
                    <Text style={styles.rentalBikeName}>{rental.bike_name}</Text>
                    <Text style={styles.rentalPlate}>Plate: {rental.vehicle_number}</Text>
                  </View>
                  {isEndingToday ? (
                    <View style={styles.endingBadge}>
                      <Text style={styles.endingBadgeText}>Ends Today</Text>
                    </View>
                  ) : (
                    <View style={styles.rentedBadge}>
                      <Text style={styles.rentedBadgeText}>On Rent</Text>
                    </View>
                  )}
                </View>

                <View style={styles.rentalCustomerRow}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.rentalLabel}>Customer</Text>
                    <Text style={styles.rentalCustomerName}>{rental.customer_name}</Text>
                  </View>
                  <TouchableOpacity 
                    style={styles.callButton}
                    onPress={() => handleCall(rental.customer_phone)}
                    activeOpacity={0.7}
                  >
                    <MaterialIcons name="call" size={16} color="#006875" />
                    <Text style={styles.callButtonText}>Call</Text>
                  </TouchableOpacity>
                </View>

                <View style={styles.rentalFooter}>
                  <MaterialIcons name="event" size={14} color="#6b7a7d" />
                  <Text style={styles.rentalDurationText}>
                    Return: {new Date(rental.end_date).toLocaleDateString()} at {new Date(rental.end_date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </Text>
                </View>
              </View>
            );
          })
        )}
        <View style={{ height: 40 }} />
      </ScrollView>

      {/* Notifications Alert Center Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={alertModalVisible}
        onRequestClose={() => setAlertModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Notification Center 📢</Text>
              <TouchableOpacity onPress={() => setAlertModalVisible(false)}>
                <MaterialIcons name="close" size={24} color="#1e293b" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalScroll} showsVerticalScrollIndicator={false}>
              {/* Returns Alerts Group */}
              <Text style={styles.modalGroupTitle}>⚠️ Today{"'"}s Returns ({endingTodayCount})</Text>
              {stats?.rental_end_alerts && stats.rental_end_alerts.length > 0 ? (
                stats.rental_end_alerts.map((alertItem: any) => (
                  <View key={`end-alert-${alertItem.booking_id}`} style={styles.modalAlertItemRed}>
                    <Text style={styles.alertItemBike}>{alertItem.bike_name}</Text>
                    <Text style={styles.alertItemText}>
                      Rented by <Text style={{ fontWeight: 'bold' }}>{alertItem.customer_name}</Text> ({alertItem.customer_phone}).
                    </Text>
                    <Text style={styles.alertItemPlate}>Plate: {alertItem.vehicle_number} | Return date is TODAY.</Text>
                    <TouchableOpacity 
                      style={styles.modalCallLink} 
                      onPress={() => handleCall(alertItem.customer_phone)}
                    >
                      <MaterialIcons name="call" size={14} color="#991b1b" />
                      <Text style={styles.modalCallLinkText}>Call Customer immediately</Text>
                    </TouchableOpacity>
                  </View>
                ))
              ) : (
                <Text style={styles.modalEmptyText}>No rentals ending today.</Text>
              )}

              {/* Maintenance Alerts Group */}
              <Text style={[styles.modalGroupTitle, { marginTop: 24 }]}>🔧 Bike Maintenance Alerts ({maintenanceCount})</Text>
              {alerts && alerts.length > 0 ? (
                alerts.map((bikeAlert: any) => (
                  <TouchableOpacity
                    key={`maint-alert-${bikeAlert.id}`}
                    style={styles.modalAlertItemBlue}
                    onPress={() => {
                      setAlertModalVisible(false);
                      router.push(`/bike/${bikeAlert.id}`);
                    }}
                  >
                    <Text style={styles.alertItemBike}>{bikeAlert.brand} {bikeAlert.name}</Text>
                    <Text style={styles.alertItemText}>
                      Scheduled maintenance date is overdue or upcoming: {bikeAlert.next_maintenance_date || 'N/A'}.
                    </Text>
                    <Text style={styles.alertItemPlate}>Plate: {bikeAlert.vehicle_number || 'N/A'}</Text>
                  </TouchableOpacity>
                ))
              ) : (
                <Text style={styles.modalEmptyText}>No bikes currently require maintenance.</Text>
              )}

              {/* Staff Activity Notifications — Admin only */}
              {isSuperuser && (
                <>
                  <View style={[styles.staffActivityHeader, { marginTop: 24 }]}>
                    <Text style={styles.modalGroupTitle}>🛎️ Staff Activity ({staffActivityCount})</Text>
                    {staffActivityCount > 0 && (
                      <TouchableOpacity
                        style={styles.markReadButton}
                        onPress={handleMarkStaffNotificationsRead}
                      >
                        <MaterialIcons name="done-all" size={14} color="#006875" />
                        <Text style={styles.markReadButtonText}>Mark All Read</Text>
                      </TouchableOpacity>
                    )}
                  </View>
                  {stats?.staff_activity_notifications && stats.staff_activity_notifications.length > 0 ? (
                    stats.staff_activity_notifications.map((notif: any) => (
                      <View key={`staff-${notif.id}`} style={styles.modalAlertItemGreen}>
                        <View style={styles.staffNotifHeader}>
                          <MaterialIcons name="person" size={14} color="#065f46" />
                          <Text style={styles.staffNotifStaff}>{notif.staff_name}</Text>
                          <Text style={styles.staffNotifLabel}>{notif.action_label}</Text>
                        </View>
                        <Text style={styles.alertItemText}>{notif.description}</Text>
                        <Text style={styles.alertItemPlate}>
                          {new Date(notif.timestamp).toLocaleDateString()} {new Date(notif.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </Text>
                      </View>
                    ))
                  ) : (
                    <Text style={styles.modalEmptyText}>No unread staff activity notifications.</Text>
                  )}
                </>
              )}
            </ScrollView>

            <TouchableOpacity 
              style={styles.modalCloseButton} 
              onPress={() => setAlertModalVisible(false)}
            >
              <Text style={styles.modalCloseButtonText}>Done</Text>
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
    backgroundColor: '#f3fbfc', // Clinical light background
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f3fbfc',
  },
  customHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 54,
    paddingBottom: 16,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e8eff1',
  },
  greetingText: {
    fontSize: 13,
    color: '#6b7a7d',
    fontWeight: '500',
  },
  brandTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#006875',
  },
  notificationBell: {
    position: 'relative',
    padding: 8,
    backgroundColor: '#f3fbfc',
    borderRadius: 24,
  },
  notificationBadge: {
    position: 'absolute',
    top: 4,
    right: 4,
    backgroundColor: '#ef4444',
    borderRadius: 10,
    minWidth: 18,
    height: 18,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  badgeText: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  container: {
    flex: 1,
    padding: 16,
  },
  warningBanner: {
    flexDirection: 'row',
    backgroundColor: '#fee2e2',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    alignItems: 'center',
  },
  warningText: {
    color: '#991b1b',
    fontSize: 12,
    fontWeight: 'bold',
    marginLeft: 8,
    flex: 1,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    borderRadius: 8,
    paddingHorizontal: 12,
    height: 48,
    shadowColor: '#6b7a7d',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
    marginBottom: 16,
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 14,
    color: '#1e293b',
    paddingVertical: 8,
  },
  clearIcon: {
    marginLeft: 8,
  },
  sectionHeader: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#006875',
    marginBottom: 12,
    letterSpacing: 0.3,
  },
  actionsBar: {
    marginBottom: 20,
    flexDirection: 'row',
  },
  actionChip: {
    alignItems: 'center',
    marginRight: 16,
    width: 72,
  },
  actionIconContainer: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  actionLabel: {
    fontSize: 11,
    color: '#1e293b',
    fontWeight: '600',
    textAlign: 'center',
  },
  financialHud: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 18,
    marginBottom: 20,
    shadowColor: '#006875',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 3,
  },
  profitHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  profitLabel: {
    fontSize: 12,
    color: '#6b7a7d',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  profitBadge: {
    backgroundColor: '#e8eff1',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  profitBadgeText: {
    fontSize: 9,
    fontWeight: 'bold',
    color: '#006875',
  },
  netProfitValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#006875',
    marginBottom: 14,
  },
  hudDividingLine: {
    height: 1,
    backgroundColor: '#e8eff1',
    marginBottom: 14,
  },
  financialRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  financialCol: {
    flex: 1,
  },
  kpiIndicatorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 6,
  },
  kpiLabel: {
    fontSize: 11,
    color: '#6b7a7d',
    fontWeight: '500',
  },
  kpiValue: {
    fontSize: 15,
    fontWeight: 'bold',
  },
  financialVerticalDivider: {
    width: 1,
    height: 30,
    backgroundColor: '#e8eff1',
    marginHorizontal: 12,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  smallCard: {
    backgroundColor: '#ffffff',
    width: '48%',
    padding: 14,
    borderRadius: 10,
    marginBottom: 12,
    shadowColor: '#6b7a7d',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2,
  },
  smallCardValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1e293b',
    marginTop: 8,
  },
  smallCardTitle: {
    fontSize: 11,
    color: '#6b7a7d',
    marginTop: 2,
  },
  rentedSectionTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionHeaderRented: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#006875',
    letterSpacing: 0.3,
  },
  rentedCountBadge: {
    backgroundColor: '#006875',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  rentedCountText: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  emptyRentalsCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 30,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#6b7a7d',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 1,
  },
  emptyRentalsText: {
    color: '#6b7a7d',
    fontSize: 13,
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 18,
  },
  rentalCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#6b7a7d',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
    borderLeftWidth: 4,
    borderLeftColor: '#006875',
  },
  rentalCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  rentalBikeName: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  rentalPlate: {
    fontSize: 12,
    color: '#6b7a7d',
    marginTop: 2,
  },
  rentedBadge: {
    backgroundColor: '#e8eff1',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  rentedBadgeText: {
    fontSize: 10,
    color: '#006875',
    fontWeight: 'bold',
  },
  endingBadge: {
    backgroundColor: '#fee2e2',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  endingBadgeText: {
    fontSize: 10,
    color: '#ef4444',
    fontWeight: 'bold',
  },
  rentalCustomerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f3fbfc',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
    marginBottom: 10,
  },
  rentalLabel: {
    fontSize: 9,
    color: '#6b7a7d',
    textTransform: 'uppercase',
  },
  rentalCustomerName: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#1e293b',
    marginTop: 1,
  },
  callButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#bac9cc',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
  },
  callButtonText: {
    fontSize: 11,
    color: '#006875',
    fontWeight: 'bold',
    marginLeft: 4,
  },
  rentalFooter: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  rentalDurationText: {
    fontSize: 12,
    color: '#6b7a7d',
    marginLeft: 6,
    fontWeight: '500',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e8eff1',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  modalScroll: {
    marginBottom: 20,
  },
  modalGroupTitle: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#006875',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  modalAlertItemRed: {
    backgroundColor: '#fee2e2',
    padding: 14,
    borderRadius: 8,
    marginBottom: 10,
  },
  modalAlertItemBlue: {
    backgroundColor: '#e0f2fe',
    padding: 14,
    borderRadius: 8,
    marginBottom: 10,
  },
  alertItemBike: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1e293b',
    marginBottom: 4,
  },
  alertItemText: {
    fontSize: 12,
    color: '#475569',
    lineHeight: 16,
  },
  alertItemPlate: {
    fontSize: 11,
    color: '#64748b',
    marginTop: 6,
  },
  modalCallLink: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    backgroundColor: '#ffffff',
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#f87171',
  },
  modalCallLinkText: {
    fontSize: 11,
    color: '#991b1b',
    fontWeight: 'bold',
    marginLeft: 4,
  },
  modalEmptyText: {
    fontSize: 12,
    color: '#6b7a7d',
    fontStyle: 'italic',
    paddingLeft: 4,
  },
  modalCloseButton: {
    backgroundColor: '#006875',
    padding: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  modalCloseButtonText: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  modalAlertItemGreen: {
    backgroundColor: '#dcfce7',
    padding: 14,
    borderRadius: 8,
    marginBottom: 10,
  },
  staffActivityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  staffNotifHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 6,
    flexWrap: 'wrap',
  },
  staffNotifStaff: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#065f46',
    marginLeft: 2,
  },
  staffNotifLabel: {
    fontSize: 11,
    color: '#047857',
    backgroundColor: '#bbf7d0',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginLeft: 6,
  },
  markReadButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    borderWidth: 1,
    borderColor: '#006875',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: '#f0fdfa',
  },
  markReadButtonText: {
    fontSize: 11,
    color: '#006875',
    fontWeight: '600',
  },
});
