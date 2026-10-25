import type { ExpoConfig } from 'expo/config';
import app from './app.json';

export default (): ExpoConfig => {
  const base = app.expo as ExpoConfig;
  return {
    ...base,
    ios: { ...base.ios, bundleIdentifier: 'com.easymoto.operations' },
    android: { ...base.android, ...(process.env.GOOGLE_SERVICES_JSON ? { googleServicesFile: process.env.GOOGLE_SERVICES_JSON } : {}) },
  };
};
