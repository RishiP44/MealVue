/**
 * API Configuration Boundary for Shelfie Mobile App
 * 
 * Networking Note:
 * - When testing on web or iOS Simulator on the same machine, 'http://127.0.0.1:8000' or 'http://localhost:8000' works.
 * - When testing on Android Emulator, use 'http://10.0.2.2:8000'.
 * - When testing on a physical mobile device via Expo Go, replace with your workstation's local LAN IP address (e.g. 'http://192.168.x.x:8000').
 */
export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export const ENDPOINTS = {
  HEALTH: `${API_BASE_URL}/api/health/`,
};
