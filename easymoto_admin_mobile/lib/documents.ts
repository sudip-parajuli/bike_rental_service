import { Platform } from 'react-native';
import api from '@/api';

function base64(bytes: Uint8Array) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
  let output = '';
  for (let i = 0; i < bytes.length; i += 3) {
    const value = (bytes[i] << 16) | ((bytes[i + 1] || 0) << 8) | (bytes[i + 2] || 0);
    output += alphabet[(value >>> 18) & 63] + alphabet[(value >>> 12) & 63] + (i + 1 < bytes.length ? alphabet[(value >>> 6) & 63] : '=') + (i + 2 < bytes.length ? alphabet[value & 63] : '=');
  }
  return output;
}
export async function openRentalDocument(id: number, kind: 'invoice' | 'contract') {
  // Authentication stays in the request header, never a shareable URL.
  const response = await api.get(`/bookings/${id}/${kind}/`, { responseType: 'arraybuffer' });
  const filename = `EasyMoto-${kind}-${id}.pdf`;
  if (Platform.OS === 'web') {
    const url = URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
    const link = document.createElement('a'); link.href = url; link.download = filename; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 10000); return;
  }
  const FileSystem = await import('expo-file-system/legacy');
  const Sharing = await import('expo-sharing');
  if (!await Sharing.isAvailableAsync()) throw new Error('Document sharing is not available on this device.');
  const uri = `${FileSystem.cacheDirectory}${filename}`;
  try {
    await FileSystem.writeAsStringAsync(uri, base64(new Uint8Array(response.data)), { encoding: FileSystem.EncodingType.Base64 });
    await Sharing.shareAsync(uri, { mimeType: 'application/pdf', dialogTitle: `Rental ${kind}` });
  } finally { await FileSystem.deleteAsync(uri, { idempotent: true }); }
}
