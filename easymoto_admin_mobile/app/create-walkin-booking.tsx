import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  Alert, 
  ScrollView, 
  ActivityIndicator, 
  TouchableOpacity, 
  TextInput,
  Platform,
  Modal
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Picker } from '@react-native-picker/picker';
import DateTimePicker, { DateTimePickerEvent } from '@react-native-community/datetimepicker';
import { MaterialIcons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { openBrowserAsync } from 'expo-web-browser';
import api from '../api';

export default function CreateWalkinBookingScreen() {
  const { phone } = useLocalSearchParams();
  const router = useRouter();

  // Collapsible section states
  const [expandedSections, setExpandedSections] = useState({
    vehicleDates: true,
    documents: false,
    checklistDeposits: false,
    guarantor: false,
    financials: false,
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Backend inventory state
  const [bikes, setBikes] = useState<any[]>([]);
  const [loadingBikes, setLoadingBikes] = useState(true);
  
  // Section 1: Vehicle & Dates State
  const [bikeId, setBikeId] = useState('');
  const today = new Date();
  const [startDate, setStartDate] = useState(new Date(today.getFullYear(), today.getMonth(), today.getDate()));
  const [endDate, setEndDate] = useState(new Date(today.getFullYear(), today.getMonth(), today.getDate()));
  const [showStartPicker, setShowStartPicker] = useState(false);
  const [showEndPicker, setShowEndPicker] = useState(false);
  const [startTime, setStartTime] = useState('09:00');
  const [endTime, setEndTime] = useState('18:00');

  // Section 2: Customer Identity State
  const [drivingLicenseNo, setDrivingLicenseNo] = useState('');
  const [docType, setDocType] = useState('Passport'); // 'Passport', 'Citizenship', 'National ID'
  const [docNumber, setDocNumber] = useState('');

  // Section 3: Checklist & Deposit State
  const [helmet, setHelmet] = useState(true);
  const [bungyCord, setBungyCord] = useState(false);
  const [maps, setMaps] = useState(false);
  
  const [depositPassport, setDepositPassport] = useState(false);
  const [depositCitizenship, setDepositCitizenship] = useState(false);
  const [depositIdCard, setDepositIdCard] = useState(false);
  const [depositOther, setDepositOther] = useState('');

  // Section 4: Guarantor Details State
  const [guarantorName, setGuarantorName] = useState('');
  const [guarantorPhone, setGuarantorPhone] = useState('');
  const [guarantorAddress, setGuarantorAddress] = useState('');

  // Section 5: Financial Overrides State
  const [manualDiscount, setManualDiscount] = useState('0');
  const [advanceAmount, setAdvanceAmount] = useState('0');
  const [paymentMethod, setPaymentMethod] = useState<'cash' | 'qr'>('cash');
  const [loading, setLoading] = useState(false);

  // Invoice success states
  const [createdInvoice, setCreatedInvoice] = useState<any>(null);
  const [successModalVisible, setSuccessModalVisible] = useState(false);

  useEffect(() => {
    fetchAvailableBikes();
    if (phone) {
      fetchCustomerDetails();
    }
  }, [phone]);

  const fetchCustomerDetails = async () => {
    try {
      const response = await api.get(`/customers/walk-in/?phone=${phone}`);
      if (response.data) {
        const cust = response.data;
        if (cust.driving_license_no) {
          setDrivingLicenseNo(cust.driving_license_no);
        }
        if (cust.passport_no) {
          if (cust.passport_no.includes(': ')) {
            const parts = cust.passport_no.split(': ');
            setDocType(parts[0]);
            setDocNumber(parts[1]);
          } else {
            setDocType('Passport');
            setDocNumber(cust.passport_no);
          }
        }
      }
    } catch (error) {
      console.log('Error fetching customer details:', error);
    }
  };

  const fetchAvailableBikes = async () => {
    try {
      const response = await api.get('/bikes/');
      const data = response.data?.results ?? response.data;
      if (Array.isArray(data)) {
        const available = data.filter((b: any) => b.availability_status === true);
        setBikes(available);
        if (available.length > 0) {
          setBikeId(available[0].id.toString());
        }
      }
    } catch (error) {
      console.log('Error fetching bikes:', error);
      Alert.alert('Error', 'Failed to load available bikes.');
    } finally {
      setLoadingBikes(false);
    }
  };

  // Pricing math calculations (client-side matching backend save logic)
  const isSameDay = startDate.toDateString() === endDate.toDateString();
  const durationDays = isSameDay ? 1 : Math.max(1, Math.round((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)) + 1);
  const selectedBike = bikes.find(b => b.id.toString() === bikeId);
  const ratePerDay = selectedBike ? parseFloat(selectedBike.price_per_day || selectedBike.rental_price_per_day || 0) : 0;
  const basePrice = ratePerDay * durationDays;

  // Calculate automatic discount percent based on duration days
  let discountPercent = 0;
  if (durationDays >= 28) discountPercent = 0.20;
  else if (durationDays >= 21) discountPercent = 0.15;
  else if (durationDays >= 14) discountPercent = 0.10;
  else if (durationDays >= 7) discountPercent = 0.05;

  const autoDiscount = basePrice * discountPercent;
  const subtotal = basePrice - autoDiscount;
  
  const manDiscountVal = parseFloat(manualDiscount) || 0;
  const finalPrice = Math.max(0, subtotal - manDiscountVal);
  
  const advAmountVal = parseFloat(advanceAmount) || 0;
  const balanceDue = Math.max(0, finalPrice - advAmountVal);

  const handleCreateBooking = async () => {
    if (!bikeId) {
      Alert.alert('Error', 'Please select an available bike/scooter.');
      return;
    }
    
    if (!drivingLicenseNo.trim()) {
      Alert.alert('Error', 'Driving License Number is required.');
      return;
    }

    setLoading(true);
    try {
      // Combine Date + Time
      const combinedStart = new Date(startDate);
      const [startH, startM] = startTime.split(':').map(Number);
      combinedStart.setHours(startH, startM, 0, 0);

      const combinedEnd = new Date(endDate);
      const [endH, endM] = endTime.split(':').map(Number);
      combinedEnd.setHours(endH, endM, 0, 0);

      if (combinedEnd <= combinedStart) {
        Alert.alert(
          'Invalid Time',
          isSameDay
            ? 'For a single-day rental, End Time must be later than Start Time (e.g. Start 09:00 AM → End 06:00 PM).'
            : 'End date and time must be after start date and time.'
        );
        setLoading(false);
        return;
      }

      const payload = {
        phone_number: phone,
        bike_id: parseInt(bikeId),
        start_date: combinedStart.toISOString(),
        end_date: combinedEnd.toISOString(),
        manual_discount: manDiscountVal,
        advance_amount: advAmountVal,
        payment_method: paymentMethod,
        driving_license_no: drivingLicenseNo,
        passport_no: docNumber ? (docType === 'Passport' ? docNumber : `${docType}: ${docNumber}`) : '',
        guarantor_name: guarantorName,
        guarantor_phone: guarantorPhone,
        guarantor_address: guarantorAddress,
        helmet,
        bungy_cord: bungyCord,
        maps,
        deposit_passport: depositPassport,
        deposit_citizenship: depositCitizenship,
        deposit_id_card: depositIdCard,
        deposit_other: depositOther
      };

      const response = await api.post('/bookings/walk-in/', payload);
      
      // Store invoice detail for the success modal
      setCreatedInvoice({
        booking_id: response.data.booking_id,
        invoice_number: response.data.invoice_number,
        total_price: response.data.total_price,
        advance_amount: response.data.advance_amount,
        balance_amount: response.data.balance_amount,
        bike_name: selectedBike ? `${selectedBike.brand} ${selectedBike.name}` : 'Bike',
        duration_days: durationDays,
        base_price: basePrice,
        auto_discount: autoDiscount,
        manual_discount: manDiscountVal
      });

      setSuccessModalVisible(true);
    } catch (error: any) {
      console.log('Booking creation error:', error);
      Alert.alert('Error', error.response?.data?.detail || JSON.stringify(error.response?.data) || 'Failed to create booking.');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenInvoice = async () => {
    if (!createdInvoice) return;
    try {
      const token = await AsyncStorage.getItem('access_token');
      const url = `${api.defaults.baseURL}/bookings/${createdInvoice.booking_id}/invoice/?token=${token}`;
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

  const handleOpenContract = async () => {
    if (!createdInvoice) return;
    try {
      const token = await AsyncStorage.getItem('access_token');
      const url = `${api.defaults.baseURL}/bookings/${createdInvoice.booking_id}/contract/?token=${token}`;
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

  const onChangeStart = (event: DateTimePickerEvent, selectedDate?: Date) => {
    setShowStartPicker(Platform.OS === 'ios');
    if (selectedDate) {
      const newStart = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate());
      setStartDate(newStart);
      
      const startD = newStart.getTime();
      const endD = new Date(endDate.getFullYear(), endDate.getMonth(), endDate.getDate()).getTime();
      if (startD > endD) {
        setEndDate(newStart);
      }
    }
  };

  const onChangeEnd = (event: DateTimePickerEvent, selectedDate?: Date) => {
    setShowEndPicker(Platform.OS === 'ios');
    if (selectedDate) {
      const newEnd = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate());
      const startD = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate()).getTime();
      const endD = newEnd.getTime();
      if (endD < startD) {
        Alert.alert('Invalid Date', 'End date cannot be before start date.');
        return;
      }
      // Same day is allowed — times will determine validity
      setEndDate(newEnd);
    }
  };

  // Custom checkbox row
  const CheckboxRow = ({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) => (
    <TouchableOpacity 
      style={styles.checkboxRow} 
      onPress={() => onChange(!value)}
      activeOpacity={0.8}
    >
      <MaterialIcons 
        name={value ? "check-box" : "check-box-outline-blank"} 
        size={24} 
        color={value ? "#006875" : "#64748b"} 
      />
      <Text style={styles.checkboxLabel}>{label}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scroll} contentContainerStyle={{ paddingBottom: 40 }} showsVerticalScrollIndicator={false}>
        <View style={styles.headerContainer}>
          <Text style={styles.header}>Walk-In Contract Form</Text>
          <Text style={styles.subtitle}>
            Registering rental contract for phone: <Text style={{ fontWeight: 'bold', color: '#006875' }}>{phone}</Text>
          </Text>
        </View>

        {/* Section 1: Vehicle and Dates */}
        <View style={styles.card}>
          <TouchableOpacity style={styles.sectionHeader} onPress={() => toggleSection('vehicleDates')} activeOpacity={0.7}>
            <View style={styles.sectionHeaderLeft}>
              <MaterialIcons name="two-wheeler" size={22} color="#006875" />
              <Text style={styles.sectionTitle}>1. Vehicle & Dates</Text>
            </View>
            <MaterialIcons 
              name={expandedSections.vehicleDates ? "keyboard-arrow-up" : "keyboard-arrow-down"} 
              size={24} 
              color="#64748b" 
            />
          </TouchableOpacity>

          {expandedSections.vehicleDates && (
            <View style={styles.sectionBody}>
              <Text style={styles.label}>Select Bike/Scooter *</Text>
              {loadingBikes ? (
                <ActivityIndicator color="#006875" style={{ marginVertical: 12 }} />
              ) : bikes.length === 0 ? (
                <Text style={styles.noBikesText}>No available bikes or scooters found.</Text>
              ) : (
                <View style={styles.pickerContainer}>
                  <Picker
                    selectedValue={bikeId}
                    onValueChange={(itemValue) => setBikeId(itemValue)}
                    style={styles.picker}
                  >
                    {bikes.map((bike) => (
                      <Picker.Item 
                        key={bike.id} 
                        label={`${bike.brand} ${bike.name} (${bike.type === 'scooter' ? 'Scooter' : 'Bike'}) - Rs. ${bike.rental_price_per_day}/day`} 
                        value={bike.id.toString()} 
                      />
                    ))}
                  </Picker>
                </View>
              )}

               <Text style={styles.label}>Start Date *</Text>
              {Platform.OS === 'web' ? (
                <input
                  type="date"
                  value={startDate.toISOString().split('T')[0]}
                  onChange={(e: any) => {
                    const d = new Date(e.target.value);
                    if (!isNaN(d.getTime())) {
                      setStartDate(d);
                      if (d > endDate) {
                        setEndDate(d);
                      }
                    }
                  }}
                  style={{
                    padding: '12px',
                    borderRadius: '8px',
                    border: '1px solid #e2e8f0',
                    backgroundColor: '#f1f5f9',
                    fontSize: '15px',
                    color: '#1e293b',
                    width: '100%',
                    boxSizing: 'border-box',
                    outline: 'none',
                  }}
                />
              ) : (
                <>
                  <TouchableOpacity style={styles.dateSelector} onPress={() => setShowStartPicker(true)}>
                    <MaterialIcons name="calendar-today" size={20} color="#006875" />
                    <Text style={styles.dateSelectorText}>
                      {startDate.toLocaleDateString()}
                    </Text>
                  </TouchableOpacity>
                  {showStartPicker && (
                    <DateTimePicker
                      value={startDate}
                      mode="date"
                      display="default"
                      onChange={onChangeStart}
                      minimumDate={new Date()}
                    />
                  )}
                </>
              )}

              <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 16, marginBottom: 4 }}>
                <Text style={styles.label}>End Date *</Text>
                <TouchableOpacity
                  style={[
                    styles.sameDayChip,
                    isSameDay && styles.sameDayChipActive
                  ]}
                  onPress={() => setEndDate(new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate()))}
                  activeOpacity={0.7}
                >
                  <MaterialIcons name="wb-sunny" size={13} color={isSameDay ? '#ffffff' : '#006875'} />
                  <Text style={[styles.sameDayChipText, isSameDay && styles.sameDayChipTextActive]}>Same Day</Text>
                </TouchableOpacity>
              </View>
              {Platform.OS === 'web' ? (
                <input
                  type="date"
                  value={endDate.toISOString().split('T')[0]}
                  min={startDate.toISOString().split('T')[0]}
                  onChange={(e: any) => {
                    const d = new Date(e.target.value);
                    if (!isNaN(d.getTime())) {
                      if (d < startDate) {
                        alert('End date cannot be before start date.');
                        return;
                      }
                      setEndDate(d);
                    }
                  }}
                  style={{
                    padding: '12px',
                    borderRadius: '8px',
                    border: '1px solid #e2e8f0',
                    backgroundColor: '#f1f5f9',
                    fontSize: '15px',
                    color: '#1e293b',
                    width: '100%',
                    boxSizing: 'border-box',
                    outline: 'none',
                  }}
                />
              ) : (
                <>
                  <TouchableOpacity style={styles.dateSelector} onPress={() => setShowEndPicker(true)}>
                    <MaterialIcons name="calendar-today" size={20} color="#006875" />
                    <Text style={styles.dateSelectorText}>
                      {endDate.toLocaleDateString()}
                    </Text>
                  </TouchableOpacity>
                  {showEndPicker && (
                    <DateTimePicker
                      value={endDate}
                      mode="date"
                      display="default"
                      onChange={onChangeEnd}
                      minimumDate={startDate}
                    />
                  )}
                </>
              )}
              {isSameDay && (
                <View style={styles.sameDayHint}>
                  <MaterialIcons name="info-outline" size={13} color="#006875" />
                  <Text style={styles.sameDayHintText}>Single-day rental — ensure End Time is after Start Time below</Text>
                </View>
              )}

              {/* Start & End Time Fields */}
              <View style={{ flexDirection: 'row', gap: 12, marginTop: 8 }}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.label}>Start Time {isSameDay ? '*' : ''}</Text>
                  <View style={[styles.pickerContainer, isSameDay && styles.pickerContainerHighlight]}>
                    <Picker
                      selectedValue={startTime}
                      onValueChange={(v) => setStartTime(v)}
                      style={styles.picker}
                    >
                      <Picker.Item label="07:00 AM" value="07:00" />
                      <Picker.Item label="08:00 AM" value="08:00" />
                      <Picker.Item label="09:00 AM" value="09:00" />
                      <Picker.Item label="10:00 AM" value="10:00" />
                      <Picker.Item label="11:00 AM" value="11:00" />
                      <Picker.Item label="12:00 PM" value="12:00" />
                      <Picker.Item label="01:00 PM" value="13:00" />
                      <Picker.Item label="02:00 PM" value="14:00" />
                      <Picker.Item label="03:00 PM" value="15:00" />
                      <Picker.Item label="04:00 PM" value="16:00" />
                      <Picker.Item label="05:00 PM" value="17:00" />
                      <Picker.Item label="06:00 PM" value="18:00" />
                      <Picker.Item label="07:00 PM" value="19:00" />
                      <Picker.Item label="08:00 PM" value="20:00" />
                    </Picker>
                  </View>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.label}>End Time {isSameDay ? '*' : ''}</Text>
                  <View style={[styles.pickerContainer, isSameDay && styles.pickerContainerHighlight]}>
                    <Picker
                      selectedValue={endTime}
                      onValueChange={(v) => setEndTime(v)}
                      style={styles.picker}
                    >
                      <Picker.Item label="07:00 AM" value="07:00" />
                      <Picker.Item label="08:00 AM" value="08:00" />
                      <Picker.Item label="09:00 AM" value="09:00" />
                      <Picker.Item label="10:00 AM" value="10:00" />
                      <Picker.Item label="11:00 AM" value="11:00" />
                      <Picker.Item label="12:00 PM" value="12:00" />
                      <Picker.Item label="01:00 PM" value="13:00" />
                      <Picker.Item label="02:00 PM" value="14:00" />
                      <Picker.Item label="03:00 PM" value="15:00" />
                      <Picker.Item label="04:00 PM" value="16:00" />
                      <Picker.Item label="05:00 PM" value="17:00" />
                      <Picker.Item label="06:00 PM" value="18:00" />
                      <Picker.Item label="07:00 PM" value="19:00" />
                      <Picker.Item label="08:00 PM" value="20:00" />
                    </Picker>
                  </View>
                </View>
              </View>
            </View>
          )}
        </View>

        {/* Section 2: Customer Identity */}
        <View style={styles.card}>
          <TouchableOpacity style={styles.sectionHeader} onPress={() => toggleSection('documents')} activeOpacity={0.7}>
            <View style={styles.sectionHeaderLeft}>
              <MaterialIcons name="badge" size={22} color="#006875" />
              <Text style={styles.sectionTitle}>2. Customer Documents</Text>
            </View>
            <MaterialIcons 
              name={expandedSections.documents ? "keyboard-arrow-up" : "keyboard-arrow-down"} 
              size={24} 
              color="#64748b" 
            />
          </TouchableOpacity>

          {expandedSections.documents && (
            <View style={styles.sectionBody}>
              <Text style={styles.label}>Driving License No. *</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter license number"
                value={drivingLicenseNo}
                onChangeText={setDrivingLicenseNo}
                placeholderTextColor="#94a3b8"
              />

              <Text style={styles.label}>Additional Document Type (Optional)</Text>
              <View style={styles.pickerContainer}>
                <Picker
                  selectedValue={docType}
                  onValueChange={(itemValue) => setDocType(itemValue)}
                  style={styles.picker}
                >
                  <Picker.Item label="Passport" value="Passport" />
                  <Picker.Item label="Citizenship Card" value="Citizenship" />
                  <Picker.Item label="National ID Card" value="National ID" />
                </Picker>
              </View>

              <Text style={styles.label}>Document Number (Optional)</Text>
              <TextInput
                style={styles.input}
                placeholder={`Enter ${docType === 'Passport' ? 'passport' : docType === 'Citizenship' ? 'citizenship' : 'national ID'} number`}
                value={docNumber}
                onChangeText={setDocNumber}
                placeholderTextColor="#94a3b8"
              />
            </View>
          )}
        </View>

        {/* Section 3: Checklist and Deposit */}
        <View style={styles.card}>
          <TouchableOpacity style={styles.sectionHeader} onPress={() => toggleSection('checklistDeposits')} activeOpacity={0.7}>
            <View style={styles.sectionHeaderLeft}>
              <MaterialIcons name="rule" size={22} color="#006875" />
              <Text style={styles.sectionTitle}>3. Checklist & Deposit</Text>
            </View>
            <MaterialIcons 
              name={expandedSections.checklistDeposits ? "keyboard-arrow-up" : "keyboard-arrow-down"} 
              size={24} 
              color="#64748b" 
            />
          </TouchableOpacity>

          {expandedSections.checklistDeposits && (
            <View style={styles.sectionBody}>
              <Text style={styles.label}>Handover Checklist</Text>
              <CheckboxRow label="Helmet Provided" value={helmet} onChange={setHelmet} />
              <CheckboxRow label="Bungy Cord Included" value={bungyCord} onChange={setBungyCord} />
              <CheckboxRow label="Local Maps Provided" value={maps} onChange={setMaps} />

              <Text style={[styles.label, { marginTop: 16 }]}>Security Deposit Kept</Text>
              <CheckboxRow label="Passport" value={depositPassport} onChange={setDepositPassport} />
              <CheckboxRow label="Citizenship Card" value={depositCitizenship} onChange={setDepositCitizenship} />
              <CheckboxRow label="National ID Card" value={depositIdCard} onChange={setDepositIdCard} />

              <Text style={[styles.label, { marginTop: 12 }]}>Other Security Deposit Description</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g. blue book, cash deposit..."
                value={depositOther}
                onChangeText={setDepositOther}
                placeholderTextColor="#94a3b8"
              />
            </View>
          )}
        </View>

        {/* Section 4: Guarantor Details */}
        <View style={styles.card}>
          <TouchableOpacity style={styles.sectionHeader} onPress={() => toggleSection('guarantor')} activeOpacity={0.7}>
            <View style={styles.sectionHeaderLeft}>
              <MaterialIcons name="security" size={22} color="#006875" />
              <Text style={styles.sectionTitle}>4. Guarantor Details (Optional)</Text>
            </View>
            <MaterialIcons 
              name={expandedSections.guarantor ? "keyboard-arrow-up" : "keyboard-arrow-down"} 
              size={24} 
              color="#64748b" 
            />
          </TouchableOpacity>

          {expandedSections.guarantor && (
            <View style={styles.sectionBody}>
              <Text style={styles.label}>Guarantor Full Name</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter guarantor's full name"
                value={guarantorName}
                onChangeText={setGuarantorName}
                placeholderTextColor="#94a3b8"
              />

              <Text style={styles.label}>Guarantor Phone No.</Text>
              <TextInput
                style={styles.input}
                placeholder="Guarantor's phone number"
                value={guarantorPhone}
                onChangeText={setGuarantorPhone}
                keyboardType="phone-pad"
                placeholderTextColor="#94a3b8"
              />

              <Text style={styles.label}>Guarantor Address</Text>
              <TextInput
                style={styles.input}
                placeholder="Guarantor's full address"
                value={guarantorAddress}
                onChangeText={setGuarantorAddress}
                placeholderTextColor="#94a3b8"
              />
            </View>
          )}
        </View>

        {/* Section 5: Financials */}
        <View style={styles.card}>
          <TouchableOpacity style={styles.sectionHeader} onPress={() => toggleSection('financials')} activeOpacity={0.7}>
            <View style={styles.sectionHeaderLeft}>
              <MaterialIcons name="payments" size={22} color="#006875" />
              <Text style={styles.sectionTitle}>5. Pricing & Discounts</Text>
            </View>
            <MaterialIcons 
              name={expandedSections.financials ? "keyboard-arrow-up" : "keyboard-arrow-down"} 
              size={24} 
              color="#64748b" 
            />
          </TouchableOpacity>

          {expandedSections.financials && (
            <View style={styles.sectionBody}>
              <View style={styles.pricingSummary}>
                <View style={styles.priceRow}>
                  <Text style={styles.priceLabel}>Daily Rate:</Text>
                  <Text style={styles.priceValue}>Rs. {ratePerDay}</Text>
                </View>
                <View style={styles.priceRow}>
                  <Text style={styles.priceLabel}>Duration:</Text>
                  <Text style={styles.priceValue}>{durationDays} {durationDays === 1 ? 'day' : 'days'}</Text>
                </View>
                <View style={styles.priceRow}>
                  <Text style={styles.priceLabel}>Base Subtotal:</Text>
                  <Text style={styles.priceValue}>Rs. {basePrice}</Text>
                </View>
                <View style={styles.priceRow}>
                  <Text style={[styles.priceLabel, { color: '#0d9488' }]}>Auto Discount ({discountPercent * 100}%):</Text>
                  <Text style={[styles.priceValue, { color: '#0d9488' }]}>- Rs. {autoDiscount}</Text>
                </View>
                <View style={styles.divider} />
                <View style={styles.priceRow}>
                  <Text style={[styles.priceLabel, { fontWeight: 'bold' }]}>Subtotal:</Text>
                  <Text style={[styles.priceValue, { fontWeight: 'bold' }]}>Rs. {subtotal}</Text>
                </View>
              </View>

              <Text style={[styles.label, { marginTop: 12 }]}>Manual Discount (Rs.)</Text>
              <TextInput
                style={styles.input}
                keyboardType="numeric"
                value={manualDiscount}
                onChangeText={setManualDiscount}
                placeholder="0"
                placeholderTextColor="#94a3b8"
              />

              <Text style={styles.label}>Advance Amount Paid (Rs.)</Text>
              <TextInput
                style={styles.input}
                keyboardType="numeric"
                value={advanceAmount}
                onChangeText={setAdvanceAmount}
                placeholder="0"
                placeholderTextColor="#94a3b8"
              />

              <View style={styles.grandSummary}>
                <View style={styles.priceRow}>
                  <Text style={styles.grandLabel}>Total Contract Price:</Text>
                  <Text style={styles.grandValue}>Rs. {finalPrice}</Text>
                </View>
                <View style={styles.priceRow}>
                  <Text style={[styles.grandLabel, { color: '#ef4444' }]}>Remaining Balance due:</Text>
                  <Text style={[styles.grandValue, { color: '#ef4444' }]}>Rs. {balanceDue}</Text>
                </View>
              </View>

              {/* Payment Method Toggle: Cash / QR */}
              <Text style={[styles.label, { marginTop: 16 }]}>Payment Method</Text>
              <View style={styles.paymentToggleRow}>
                <TouchableOpacity
                  style={[styles.paymentToggleBtn, paymentMethod === 'cash' && styles.paymentToggleBtnActive]}
                  onPress={() => setPaymentMethod('cash')}
                  activeOpacity={0.8}
                >
                  <MaterialIcons name="payments" size={20} color={paymentMethod === 'cash' ? '#ffffff' : '#006875'} />
                  <Text style={[styles.paymentToggleBtnText, paymentMethod === 'cash' && styles.paymentToggleBtnTextActive]}>Cash</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.paymentToggleBtn, paymentMethod === 'qr' && styles.paymentToggleBtnActive]}
                  onPress={() => setPaymentMethod('qr')}
                  activeOpacity={0.8}
                >
                  <MaterialIcons name="qr-code" size={20} color={paymentMethod === 'qr' ? '#ffffff' : '#006875'} />
                  <Text style={[styles.paymentToggleBtnText, paymentMethod === 'qr' && styles.paymentToggleBtnTextActive]}>QR Payment</Text>
                </TouchableOpacity>
              </View>

              {paymentMethod === 'cash' ? (
                /* Cash payment info */
                <View style={styles.cashInfoBox}>
                  <MaterialIcons name="payments" size={32} color="#006875" />
                  <Text style={styles.cashInfoText}>Collect cash payment of</Text>
                  <Text style={styles.cashInfoAmount}>Rs. {finalPrice}</Text>
                  <Text style={styles.cashInfoSubText}>Enter the advance amount received above</Text>
                </View>
              ) : (
                /* QR payment section */
                <View style={styles.qrBox}>
                  <Text style={styles.qrSubText}>Scan using eSewa or Mobile Banking</Text>
                  <Text style={styles.qrText}>📱</Text>
                  <Text style={styles.qrAmount}>Rs. {finalPrice}</Text>
                </View>
              )}

              {/* Mark as Fully Paid button — shown for both methods */}
              <TouchableOpacity
                style={styles.markPaidInsideButton}
                onPress={() => {
                  setAdvanceAmount(finalPrice.toString());
                  Alert.alert('Success', `Full payment of Rs. ${finalPrice} has been marked!`);
                }}
                activeOpacity={0.8}
              >
                <MaterialIcons name="check-circle" size={18} color="#ffffff" />
                <Text style={styles.markPaidInsideText}>Mark as Fully Paid</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Submit Actions */}
        <View style={{ paddingHorizontal: 4, marginTop: 12 }}>
          <TouchableOpacity 
            style={[styles.button, (!bikeId || bikes.length === 0) && styles.disabledButton]} 
            onPress={handleCreateBooking}
            disabled={loading || bikes.length === 0}
            activeOpacity={0.8}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Generate Contract</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.button, styles.cancelButton]} 
            onPress={() => router.back()}
            disabled={loading}
            activeOpacity={0.8}
          >
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>

      {/* SUCCESS CONTRACT & INVOICE SUMMARY MODAL */}
      <Modal animationType="slide" transparent visible={successModalVisible} onRequestClose={() => setSuccessModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <View style={styles.modalHeaderTitleRow}>
                <MaterialIcons name="check-circle" size={24} color="#10b981" />
                <Text style={styles.modalTitle}>Booking & Contract Created!</Text>
              </View>
              <TouchableOpacity onPress={() => { setSuccessModalVisible(false); router.push('/(tabs)/bookings'); }}>
                <MaterialIcons name="close" size={24} color="#1e293b" />
              </TouchableOpacity>
            </View>

            {createdInvoice && (
              <ScrollView style={styles.modalScroll} showsVerticalScrollIndicator={false}>
                <View style={styles.invoiceCard}>
                  <View style={styles.invoiceHeader}>
                    <Text style={styles.invoiceLogo}>EasyMoto Hub</Text>
                    <Text style={styles.invoiceNo}>Invoice: #{createdInvoice.invoice_number}</Text>
                  </View>
                  <View style={styles.invoiceDivider} />

                  <Text style={styles.invoiceSectionTitle}>Rental Information</Text>
                  <View style={styles.invoiceRow}>
                    <Text style={styles.invoiceLabel}>Vehicle:</Text>
                    <Text style={styles.invoiceValue}>{createdInvoice.bike_name}</Text>
                  </View>
                  <View style={styles.invoiceRow}>
                    <Text style={styles.invoiceLabel}>Duration:</Text>
                    <Text style={styles.invoiceValue}>{createdInvoice.duration_days} days</Text>
                  </View>
                  <View style={styles.invoiceRow}>
                    <Text style={styles.invoiceLabel}>Start Date:</Text>
                    <Text style={styles.invoiceValue}>{startDate.toLocaleDateString()}</Text>
                  </View>
                  <View style={styles.invoiceRow}>
                    <Text style={styles.invoiceLabel}>End Date:</Text>
                    <Text style={styles.invoiceValue}>{endDate.toLocaleDateString()}</Text>
                  </View>

                  <View style={styles.invoiceDivider} />
                  <Text style={styles.invoiceSectionTitle}>Charges Breakdown</Text>
                  
                  <View style={styles.invoiceRow}>
                    <Text style={styles.invoiceLabel}>Base Rental Rate:</Text>
                    <Text style={styles.invoiceValue}>Rs. {createdInvoice.base_price}</Text>
                  </View>
                  <View style={styles.invoiceRow}>
                    <Text style={styles.invoiceLabel}>Duration Auto Discount:</Text>
                    <Text style={[styles.invoiceValue, { color: '#0d9488' }]}>- Rs. {createdInvoice.auto_discount}</Text>
                  </View>
                  <View style={styles.invoiceRow}>
                    <Text style={styles.invoiceLabel}>Additional Manual Discount:</Text>
                    <Text style={[styles.invoiceValue, { color: '#0d9488' }]}>- Rs. {createdInvoice.manual_discount}</Text>
                  </View>

                  <View style={styles.invoiceDivider} />
                  
                  <View style={styles.invoiceRow}>
                    <Text style={[styles.invoiceLabel, { fontWeight: 'bold' }]}>Grand Net Total:</Text>
                    <Text style={[styles.invoiceValue, { fontWeight: 'bold', color: '#006875' }]}>Rs. {createdInvoice.total_price}</Text>
                  </View>
                  <View style={styles.invoiceRow}>
                    <Text style={styles.invoiceLabel}>Advance Amount Paid:</Text>
                    <Text style={styles.invoiceValue}>Rs. {createdInvoice.advance_amount}</Text>
                  </View>
                  <View style={styles.invoiceRow}>
                    <Text style={[styles.invoiceLabel, { fontWeight: 'bold', color: '#ef4444' }]}>Balance Due:</Text>
                    <Text style={[styles.invoiceValue, { fontWeight: 'bold', color: '#ef4444' }]}>Rs. {createdInvoice.balance_amount}</Text>
                  </View>
                </View>
                
                <Text style={styles.invoiceDisclaimer}>
                  A digital rental contract and invoice have been sent to the customer{"'"}s email. Please collect deposits and print if required.
                </Text>
              </ScrollView>
            )}

            <View style={styles.printButtonsRow}>
              <TouchableOpacity style={styles.printButton} onPress={handleOpenInvoice} activeOpacity={0.7}>
                <MaterialIcons name="print" size={18} color="#006875" />
                <Text style={styles.printButtonText}>Print Invoice</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.printButton} onPress={handleOpenContract} activeOpacity={0.7}>
                <MaterialIcons name="description" size={18} color="#006875" />
                <Text style={styles.printButtonText}>Print Contract</Text>
              </TouchableOpacity>
            </View>

            <TouchableOpacity 
              style={styles.modalDoneButton} 
              onPress={() => {
                setSuccessModalVisible(false);
                router.push('/(tabs)/bookings');
              }}
            >
              <Text style={styles.modalDoneButtonText}>Close & Return to Bookings</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3fbfc',
  },
  scroll: {
    flex: 1,
    padding: 16,
  },
  headerContainer: {
    marginBottom: 20,
    marginTop: 10,
  },
  header: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#006875',
  },
  subtitle: {
    fontSize: 14,
    color: '#6b7a7d',
    marginTop: 4,
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#6b7a7d',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2,
    overflow: 'hidden',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#ffffff',
  },
  sectionHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  sectionBody: {
    padding: 16,
    paddingTop: 0,
    borderTopWidth: 1,
    borderTopColor: '#f1f5f9',
    backgroundColor: '#ffffff',
  },
  label: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#475569',
    marginTop: 16,
    marginBottom: 8,
  },
  pickerContainer: {
    backgroundColor: '#f1f5f9',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    justifyContent: 'center',
  },
  picker: {
    width: '100%',
    color: '#1e293b',
  },
  noBikesText: {
    color: '#ef4444',
    fontSize: 14,
    fontWeight: '500',
  },
  dateSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f1f5f9',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    padding: 12,
    borderRadius: 8,
  },
  dateSelectorText: {
    fontSize: 16,
    color: '#334155',
    marginLeft: 10,
  },
  input: {
    backgroundColor: '#f1f5f9',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    padding: 12,
    borderRadius: 8,
    fontSize: 15,
    color: '#1e293b',
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    gap: 8,
  },
  checkboxLabel: {
    fontSize: 14,
    color: '#475569',
  },
  pricingSummary: {
    backgroundColor: '#f8fafc',
    borderRadius: 8,
    padding: 12,
    marginTop: 14,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    gap: 6,
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  priceLabel: {
    fontSize: 13,
    color: '#64748b',
  },
  priceValue: {
    fontSize: 13,
    fontWeight: '500',
    color: '#1e293b',
  },
  divider: {
    height: 1,
    backgroundColor: '#e2e8f0',
    marginVertical: 4,
  },
  grandSummary: {
    backgroundColor: '#f0fdfa',
    borderRadius: 8,
    padding: 12,
    marginTop: 16,
    borderWidth: 1,
    borderColor: '#ccfbf1',
    gap: 8,
  },
  grandLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#0d9488',
  },
  grandValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#006875',
  },
  button: {
    backgroundColor: '#006875',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  disabledButton: {
    backgroundColor: '#94a3b8',
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  cancelButton: {
    backgroundColor: '#e2e8f0',
    marginTop: 12,
  },
  cancelButtonText: {
    color: '#475569',
    fontWeight: 'bold',
    fontSize: 16,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
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
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
    paddingBottom: 12,
  },
  modalHeaderTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  modalScroll: {
    marginBottom: 20,
  },
  invoiceCard: {
    backgroundColor: '#f8fafc',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    padding: 16,
  },
  invoiceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  invoiceLogo: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#006875',
  },
  invoiceNo: {
    fontSize: 12,
    color: '#64748b',
  },
  invoiceDivider: {
    height: 1,
    borderStyle: 'dashed',
    borderWidth: 1,
    borderColor: '#cbd5e1',
    marginVertical: 12,
  },
  invoiceSectionTitle: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#64748b',
    textTransform: 'uppercase',
    marginBottom: 8,
    letterSpacing: 0.5,
  },
  invoiceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginVertical: 4,
  },
  invoiceLabel: {
    fontSize: 13,
    color: '#475569',
  },
  invoiceValue: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1e293b',
  },
  invoiceDisclaimer: {
    fontSize: 12,
    color: '#64748b',
    textAlign: 'center',
    lineHeight: 18,
    marginTop: 16,
    paddingHorizontal: 12,
  },
  modalDoneButton: {
    backgroundColor: '#006875',
    paddingVertical: 14,
    borderRadius: 10,
    width: '100%',
    alignItems: 'center',
  },
  modalDoneButtonText: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: 15,
  },
  printButtonsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
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
  qrSectionContainer: {
    marginTop: 16,
    alignItems: 'center',
    backgroundColor: '#f8fafc',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#cbd5e1',
    padding: 16,
  },
  qrPlaceholderSmall: {
    width: 140,
    height: 140,
    backgroundColor: '#ffffff',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#bac9cc',
    borderStyle: 'dashed',
  },
  qrText: {
    fontSize: 32,
  },
  qrSubText: {
    fontSize: 10,
    color: '#6b7a7d',
    marginTop: 4,
    textAlign: 'center',
    paddingHorizontal: 8,
  },
  qrAmount: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#006875',
    marginTop: 4,
  },
  sameDayChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    borderWidth: 1.5,
    borderColor: '#006875',
    borderRadius: 20,
    paddingVertical: 4,
    paddingHorizontal: 10,
    backgroundColor: '#ffffff',
  },
  sameDayChipActive: {
    backgroundColor: '#006875',
  },
  sameDayChipText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#006875',
  },
  sameDayChipTextActive: {
    color: '#ffffff',
  },
  sameDayHint: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#e0f7fa',
    borderRadius: 6,
    paddingVertical: 7,
    paddingHorizontal: 10,
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#b2ebf2',
  },
  sameDayHintText: {
    fontSize: 12,
    color: '#006875',
    flex: 1,
    lineHeight: 16,
  },
  pickerContainerHighlight: {
    borderColor: '#006875',
    borderWidth: 1.5,
  },

  /* Payment method toggle */
  paymentToggleRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 8,
    marginBottom: 12,
  },
  paymentToggleBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: '#006875',
    backgroundColor: '#ffffff',
  },
  paymentToggleBtnActive: {
    backgroundColor: '#006875',
    borderColor: '#006875',
  },
  paymentToggleBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#006875',
  },
  paymentToggleBtnTextActive: {
    color: '#ffffff',
  },

  /* Cash info box */
  cashInfoBox: {
    alignItems: 'center',
    backgroundColor: '#f0fdfa',
    borderWidth: 1,
    borderColor: '#99f6e4',
    borderRadius: 10,
    paddingVertical: 20,
    paddingHorizontal: 16,
    marginBottom: 12,
    gap: 4,
  },
  cashInfoText: {
    fontSize: 13,
    color: '#475569',
    marginTop: 6,
  },
  cashInfoAmount: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#006875',
  },
  cashInfoSubText: {
    fontSize: 11,
    color: '#64748b',
    textAlign: 'center',
    marginTop: 4,
  },

  /* QR box */
  qrBox: {
    alignItems: 'center',
    backgroundColor: '#f8fafc',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 10,
    paddingVertical: 16,
    paddingHorizontal: 12,
    marginBottom: 12,
    gap: 4,
  },

  /* Mark as paid button */
  markPaidInsideButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#0d9488',
    borderRadius: 8,
    paddingVertical: 12,
    marginTop: 4,
    width: '100%',
  },
  markPaidInsideText: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: 13,
  },
});
