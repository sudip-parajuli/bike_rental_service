import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ScrollView, ActivityIndicator } from 'react-native';
import api from '../api';
import { useRouter } from 'expo-router';

export default function CreateCustomerScreen() {
  const [phone, setPhone] = useState('');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleCreateCustomer = async () => {
    if (!phone || !fullName) {
      Alert.alert('Error', 'Phone and Full Name are required');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/customers/walk-in/', {
        phone_number: phone,
        full_name: fullName,
        email: email,
        nationality: 'Nepali',
      });
      
      Alert.alert('Success', response.data.detail);
      const userPhone = response.data.phone_number;
      
      // Reset form
      setFullName('');
      setEmail('');
      setPhone('');
      
      // Navigate to booking creation passing phone number
      router.push({
        pathname: '/create-walkin-booking',
        params: { phone: userPhone }
      });

    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to create customer');
      console.log(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.header}>Add Walk-in Customer</Text>
      <Text style={styles.subtitle}>
        Enter the customer{"'"}s phone number. If they are new, their account will be created and they will receive an email with their temporary credentials.
      </Text>

      <View style={styles.form}>
        <Text style={styles.label}>Phone Number *</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g. 9800000000"
          value={phone}
          onChangeText={setPhone}
          keyboardType="phone-pad"
        />

        <Text style={styles.label}>Full Name *</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g. Ram Bahadur"
          value={fullName}
          onChangeText={setFullName}
        />

        <Text style={styles.label}>Email Address (Optional)</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g. ram@example.com"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
        />

        <TouchableOpacity 
          style={styles.button} 
          onPress={handleCreateCustomer}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Search & Create Customer</Text>
          )}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
    padding: 16,
  },
  header: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1e293b',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#64748b',
    marginBottom: 24,
    lineHeight: 20,
  },
  form: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  label: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#334155',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#f1f5f9',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    fontSize: 16,
  },
  button: {
    backgroundColor: '#006875',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
});
