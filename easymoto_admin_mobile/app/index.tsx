import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';
import api from '../api';

// Show the API URL in dev mode to help with debugging
const API_BASE = Platform.OS === 'web'
  ? 'http://localhost:8000/api/mobile'
  : 'https://easymoto.com.np/api/mobile';

export default function LoginScreen() {
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const token = await AsyncStorage.getItem('access_token');
      if (token) {
        router.replace('/(tabs)');
      }
      setCheckingAuth(false);
    };
    checkAuth();
  }, []);

  const handleLogin = async () => {
    if (!login || !password) {
      Alert.alert('Missing Fields', 'Please enter your username/email and password.');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/auth/login/', { login, password });
      const { access, refresh, is_superuser, is_staff, username, full_name, email } = response.data;
      await AsyncStorage.setItem('access_token', access);
      await AsyncStorage.setItem('refresh_token', refresh);
      await AsyncStorage.setItem('is_superuser', is_superuser ? 'true' : 'false');
      await AsyncStorage.setItem('is_staff', is_staff ? 'true' : 'false');
      await AsyncStorage.setItem('username', username || login);
      await AsyncStorage.setItem('full_name', full_name || username || login);
      await AsyncStorage.setItem('email', email || '');
      router.replace('/(tabs)');
    } catch (error: any) {
      // Show detailed error so user knows exactly what went wrong
      const serverMsg =
        error.response?.data?.non_field_errors?.[0] ||
        error.response?.data?.detail ||
        error.response?.data?.login?.[0] ||
        error.response?.data?.password?.[0] ||
        JSON.stringify(error.response?.data || {});
      const networkMsg = error.message || 'Unknown error';
      const statusCode = error.response?.status || 'No response';
      Alert.alert(
        'Login Failed',
        `Status: ${statusCode}\n\nServer: ${serverMsg || networkMsg}\n\nURL: ${API_BASE}/auth/login/`,
        [{ text: 'OK' }]
      );
    } finally {
      setLoading(false);
    }
  };

  if (checkingAuth) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#3b82f6" />
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={{ flexGrow: 1, justifyContent: 'center', alignItems: 'center', padding: 20 }}>
      <View style={styles.card}>
        <View style={styles.logoContainer}>
          <Text style={styles.logo}>🏍️</Text>
        </View>
        <Text style={styles.title}>EasyMoto Admin</Text>
        <Text style={styles.subtitle}>Staff & Administrator Login</Text>

        {/* Debug URL indicator */}
        <View style={styles.debugBadge}>
          <Text style={styles.debugText}>🔗 {Platform.OS === 'web' ? 'localhost:8000' : 'easymoto.com.np'}</Text>
        </View>

        <View style={styles.inputWrapper}>
          <Text style={styles.label}>Username or Email</Text>
          <TextInput
            id="login-username"
            style={styles.input}
            placeholder="e.g. Easymoto or admin@email.com"
            value={login}
            onChangeText={setLogin}
            autoCapitalize="none"
            autoCorrect={false}
          />
        </View>

        <View style={styles.inputWrapper}>
          <Text style={styles.label}>Password</Text>
          <TextInput
            id="login-password"
            style={styles.input}
            placeholder="Your password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />
        </View>

        <TouchableOpacity style={styles.button} onPress={handleLogin} disabled={loading}>
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Log In</Text>
          )}
        </TouchableOpacity>

        <View style={styles.hint}>
          <Text style={styles.hintText}>⚠️ Admin access only. Regular customer accounts cannot log in here.</Text>
        </View>
      </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f172a',
    padding: 20,
  },
  card: {
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 32,
    width: '100%',
    maxWidth: 420,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 16,
    elevation: 10,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 12,
  },
  logo: {
    fontSize: 52,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#f1f5f9',
    textAlign: 'center',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#94a3b8',
    textAlign: 'center',
    marginBottom: 28,
  },
  inputWrapper: {
    marginBottom: 16,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: '#94a3b8',
    marginBottom: 6,
  },
  input: {
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#334155',
    padding: 14,
    borderRadius: 10,
    fontSize: 15,
    color: '#f1f5f9',
  },
  button: {
    backgroundColor: '#3b82f6',
    padding: 16,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  hint: {
    marginTop: 20,
    padding: 12,
    backgroundColor: '#1e3a5f',
    borderRadius: 8,
  },
  hintText: {
    color: '#93c5fd',
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
  debugBadge: {
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
    alignSelf: 'center',
    marginBottom: 20,
  },
  debugText: {
    color: '#64748b',
    fontSize: 11,
    fontFamily: 'monospace' as any,
  },
});
