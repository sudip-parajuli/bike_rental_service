import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  SafeAreaView,
  Dimensions,
  Platform,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import { MaterialIcons } from '@expo/vector-icons';

const { width } = Dimensions.get('window');

// Dictionary to satisfy internationalization warnings and localize strings
const TRANSLATIONS = {
  accountSettings: 'Account Settings',
  manageSession: 'Manage your session',
  administrator: 'Administrator',
  staffMember: 'Staff Member',
  personalCredentials: 'Personal Credentials',
  fullName: 'Full Name',
  username: 'Username',
  emailAddress: 'Email Address',
  systemPermissions: 'System Permissions',
  accountRole: 'Account Role',
  financialVisibility: 'Financial Visibility',
  logOutSession: 'Log Out Session',
  appVersion: 'EasyMoto Admin Mobile • Version 1.0.0',
  confirmLogoutTitle: 'Confirm Logout',
  confirmLogoutMsg: 'Are you sure you want to log out of EasyMoto Admin?',
  cancel: 'Cancel',
  logout: 'Log Out',
  fullAccess: 'Administrator (Full Access)',
  standardAccess: 'Staff Associate (Standard Access)',
  hudVisible: 'Authorized (Revenue/Profit HUD Visible)',
  hudHidden: 'Restricted (Hidden)',
  noEmail: 'N/A',
};

export default function ProfileScreen() {
  const [profile, setProfile] = useState({
    fullName: '',
    username: '',
    email: '',
    isSuperuser: false,
    isStaff: false,
  });
  const router = useRouter();

  useEffect(() => {
    const loadProfileData = async () => {
      const superuserVal = await AsyncStorage.getItem('is_superuser');
      const staffVal = await AsyncStorage.getItem('is_staff');
      const nameVal = await AsyncStorage.getItem('full_name') || 'Admin';
      const usernameVal = await AsyncStorage.getItem('username') || '';
      const emailVal = await AsyncStorage.getItem('email') || '';

      setProfile({
        fullName: nameVal,
        username: usernameVal,
        email: emailVal,
        isSuperuser: superuserVal === 'true',
        isStaff: staffVal === 'true',
      });
    };
    loadProfileData();
  }, []);

  const performLogoutAction = async () => {
    try {
      // Clear auth and profile credentials
      await AsyncStorage.multiRemove([
        'access_token',
        'refresh_token',
        'is_superuser',
        'is_staff',
        'username',
        'full_name',
        'email',
      ]);
      router.replace('/');
    } catch (error) {
      console.log('Error clearing session:', error);
      alert('Failed to log out successfully.');
    }
  };

  const handleLogout = () => {
    if (Platform.OS === 'web') {
      if (window.confirm(TRANSLATIONS.confirmLogoutMsg)) {
        performLogoutAction();
      }
    } else {
      Alert.alert(
        TRANSLATIONS.confirmLogoutTitle,
        TRANSLATIONS.confirmLogoutMsg,
        [
          {
            text: TRANSLATIONS.cancel,
            style: 'cancel',
          },
          {
            text: TRANSLATIONS.logout,
            style: 'destructive',
            onPress: performLogoutAction,
          },
        ]
      );
    }
  };

  // Get user initials for avatar
  const getInitials = (name: string) => {
    if (!name) return 'U';
    const parts = name.split(' ').filter(Boolean);
    if (parts.length > 1) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  const initials = profile.fullName ? getInitials(profile.fullName) : 'EM';

  return (
    <SafeAreaView style={styles.safeContainer}>
      {/* Custom Premium Header */}
      <View style={styles.customHeader}>
        <Text style={styles.headerTitle}>{TRANSLATIONS.accountSettings}</Text>
        <Text style={styles.headerSubtitle}>{TRANSLATIONS.manageSession}</Text>
      </View>

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Avatar Card Section */}
        <View style={styles.profileCard}>
          <View style={styles.avatarContainer}>
            <Text style={styles.avatarText}>{initials}</Text>
          </View>
          <Text style={styles.userFullName}>{profile.fullName}</Text>
          <Text style={styles.userUsername}>@{profile.username}</Text>

          {/* Role Pills */}
          <View style={styles.badgeRow}>
            {profile.isSuperuser && (
              <View style={[styles.badge, styles.adminBadge]}>
                <MaterialIcons name="security" size={12} color="#ffffff" />
                <Text style={styles.badgeText}>{TRANSLATIONS.administrator}</Text>
              </View>
            )}
            {profile.isStaff && (
              <View style={[styles.badge, styles.staffBadge]}>
                <MaterialIcons name="badge" size={12} color="#006875" />
                <Text style={[styles.badgeText, { color: '#006875' }]}>{TRANSLATIONS.staffMember}</Text>
              </View>
            )}
          </View>
        </View>

        {/* Account Details Section */}
        <Text style={styles.sectionHeader}>{TRANSLATIONS.personalCredentials}</Text>
        <View style={styles.detailCard}>
          <View style={styles.detailRow}>
            <View style={styles.detailIconBox}>
              <MaterialIcons name="person-outline" size={20} color="#006875" />
            </View>
            <View style={styles.detailCol}>
              <Text style={styles.detailLabel}>{TRANSLATIONS.fullName}</Text>
              <Text style={styles.detailValue}>{profile.fullName}</Text>
            </View>
          </View>

          <View style={styles.divider} />

          <View style={styles.detailRow}>
            <View style={styles.detailIconBox}>
              <MaterialIcons name="alternate-email" size={20} color="#006875" />
            </View>
            <View style={styles.detailCol}>
              <Text style={styles.detailLabel}>{TRANSLATIONS.username}</Text>
              <Text style={styles.detailValue}>{profile.username}</Text>
            </View>
          </View>

          <View style={styles.divider} />

          <View style={styles.detailRow}>
            <View style={styles.detailIconBox}>
              <MaterialIcons name="mail-outline" size={20} color="#006875" />
            </View>
            <View style={styles.detailCol}>
              <Text style={styles.detailLabel}>{TRANSLATIONS.emailAddress}</Text>
              <Text style={styles.detailValue}>{profile.email || TRANSLATIONS.noEmail}</Text>
            </View>
          </View>
        </View>

        {/* Security Permissions Info Card */}
        <Text style={styles.sectionHeader}>{TRANSLATIONS.systemPermissions}</Text>
        <View style={styles.detailCard}>
          <View style={styles.detailRow}>
            <View style={styles.detailIconBox}>
              <MaterialIcons name="verified-user" size={20} color="#006875" />
            </View>
            <View style={styles.detailCol}>
              <Text style={styles.detailLabel}>{TRANSLATIONS.accountRole}</Text>
              <Text style={styles.detailValue}>
                {profile.isSuperuser ? TRANSLATIONS.fullAccess : TRANSLATIONS.standardAccess}
              </Text>
            </View>
          </View>

          <View style={styles.divider} />

          <View style={styles.detailRow}>
            <View style={styles.detailIconBox}>
              <MaterialIcons name="attach-money" size={20} color="#006875" />
            </View>
            <View style={styles.detailCol}>
              <Text style={styles.detailLabel}>{TRANSLATIONS.financialVisibility}</Text>
              <Text style={styles.detailValue}>
                {profile.isSuperuser ? TRANSLATIONS.hudVisible : TRANSLATIONS.hudHidden}
              </Text>
            </View>
          </View>
        </View>

        {/* Logout Action Button */}
        <TouchableOpacity
          style={styles.logoutButton}
          onPress={handleLogout}
          activeOpacity={0.8}
        >
          <MaterialIcons name="logout" size={20} color="#ffffff" style={styles.logoutIcon} />
          <Text style={styles.logoutButtonText}>{TRANSLATIONS.logOutSession}</Text>
        </TouchableOpacity>

        <Text style={styles.appVersionText}>{TRANSLATIONS.appVersion}</Text>
        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeContainer: {
    flex: 1,
    backgroundColor: '#f3fbfc', // Clinical light background
  },
  customHeader: {
    paddingHorizontal: 24,
    paddingTop: 54,
    paddingBottom: 20,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e8eff1',
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
    fontWeight: '500',
  },
  container: {
    flex: 1,
    paddingHorizontal: 20,
  },
  scrollContent: {
    paddingTop: 20,
  },
  profileCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    paddingVertical: 28,
    paddingHorizontal: 20,
    alignItems: 'center',
    marginBottom: 24,
    shadowColor: '#6b7a7d',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 12,
    elevation: 3,
  },
  avatarContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#006875',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
    shadowColor: '#006875',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  avatarText: {
    color: '#ffffff',
    fontSize: 28,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
  userFullName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1e293b',
    marginBottom: 4,
  },
  userUsername: {
    fontSize: 13,
    color: '#6b7a7d',
    fontWeight: '500',
    marginBottom: 16,
  },
  badgeRow: {
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'center',
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  adminBadge: {
    backgroundColor: '#dc2626', // Premium Red badge
  },
  staffBadge: {
    backgroundColor: '#e0f2fe', // Premium blue badge
  },
  badgeText: {
    color: '#ffffff',
    fontSize: 11,
    fontWeight: 'bold',
  },
  sectionHeader: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#006875',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 10,
    paddingLeft: 4,
  },
  detailCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 4,
    marginBottom: 24,
    shadowColor: '#6b7a7d',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
  },
  detailIconBox: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#f0fdfa',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  detailCol: {
    flex: 1,
  },
  detailLabel: {
    fontSize: 11,
    color: '#6b7a7d',
    fontWeight: '500',
    marginBottom: 2,
  },
  detailValue: {
    fontSize: 14,
    color: '#1e293b',
    fontWeight: 'bold',
  },
  divider: {
    height: 1,
    backgroundColor: '#e8eff1',
  },
  logoutButton: {
    backgroundColor: '#dc2626',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    marginTop: 8,
    marginBottom: 20,
    shadowColor: '#dc2626',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 3,
  },
  logoutIcon: {
    marginRight: 8,
  },
  logoutButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  appVersionText: {
    fontSize: 11,
    color: '#6b7a7d',
    textAlign: 'center',
    marginTop: 10,
    fontWeight: '500',
  },
});
