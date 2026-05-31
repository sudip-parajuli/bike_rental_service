import React, { useEffect, useState } from 'react';
import { Tabs, useRouter } from 'expo-router';
// Using an existing icon set since create-expo-app gives you vector-icons by default
import { MaterialIcons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { View, ActivityIndicator } from 'react-native';

export default function TabLayout() {
  const [checkingAuth, setCheckingAuth] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const checkToken = async () => {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) {
        router.replace('/');
      } else {
        setCheckingAuth(false);
      }
    };
    checkToken();
  }, []);

  if (checkingAuth) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f3fbfc' }}>
        <ActivityIndicator size="large" color="#006875" />
      </View>
    );
  }
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#006875',
        tabBarInactiveTintColor: '#6b7a7d',
        tabBarStyle: {
          backgroundColor: '#ffffff',
          borderTopWidth: 1,
          borderTopColor: '#bac9cc',
          height: 60,
          paddingBottom: 8,
          paddingTop: 8,
        },
        headerShown: false, // We will build beautiful headers directly in our screens for a premium custom feel
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Dashboard',
          tabBarIcon: ({ color }) => <MaterialIcons name="dashboard" size={24} color={color} />,
        }}
      />
      <Tabs.Screen
        name="bikes"
        options={{
          title: 'Inventory',
          tabBarIcon: ({ color }) => <MaterialIcons name="two-wheeler" size={24} color={color} />,
        }}
      />
      <Tabs.Screen
        name="bookings"
        options={{
          title: 'Bookings',
          tabBarIcon: ({ color }) => <MaterialIcons name="book-online" size={24} color={color} />,
        }}
      />
      <Tabs.Screen
        name="customers"
        options={{
          title: 'Customers',
          tabBarIcon: ({ color }) => <MaterialIcons name="people" size={24} color={color} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color }) => <MaterialIcons name="person" size={24} color={color} />,
        }}
      />
    </Tabs>
  );
}
