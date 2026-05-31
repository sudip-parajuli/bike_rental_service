import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';

// In a real app, use an environment variable or Expo Constants.
// If you are using a physical device, 127.0.0.1 WILL NOT WORK.
// You MUST replace 127.0.0.1 with your computer's local Wi-Fi IP address.
import { Platform } from 'react-native';

const API_URL = Platform.OS === 'web' 
  ? 'http://localhost:8000/api/mobile' 
  : 'http://192.168.10.65:8000/api/mobile'; 

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response && error.response.status === 401) {
      // Token is invalid or expired, logout user
      await AsyncStorage.removeItem('access_token');
      await AsyncStorage.removeItem('refresh_token');
      router.replace('/');
    }
    return Promise.reject(error);
  }
);

export default api;
