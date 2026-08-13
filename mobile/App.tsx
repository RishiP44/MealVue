import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, ActivityIndicator, TouchableOpacity } from 'react-native';
import { ENDPOINTS } from './src/config/api';

export default function App() {
  const [status, setStatus] = useState<string>('Checking...');
  const [loading, setLoading] = useState<boolean>(true);

  const checkHealth = async () => {
    setLoading(true);
    try {
      const response = await fetch(ENDPOINTS.HEALTH);
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'ok') {
          setStatus('Connected (200 OK)');
        } else {
          setStatus(`Unexpected response: ${JSON.stringify(data)}`);
        }
      } else {
        setStatus(`HTTP ${response.status} Error`);
      }
    } catch (error: any) {
      setStatus(`Connection failed: ${error.message || 'Network error'}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Shelfie</Text>
      <Text style={styles.subtitle}>Phase 1 Foundation & Connectivity Test</Text>
      
      <View style={styles.card}>
        <Text style={styles.label}>Backend Status:</Text>
        {loading ? (
          <ActivityIndicator size="small" color="#2563EB" style={styles.spinner} />
        ) : (
          <Text style={[styles.statusText, status.includes('Connected') ? styles.success : styles.failure]}>
            {status}
          </Text>
        )}
      </View>

      <TouchableOpacity style={styles.button} onPress={checkHealth} disabled={loading}>
        <Text style={styles.buttonText}>Recheck Connection</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#0F172A',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#64748B',
    marginBottom: 32,
    textAlign: 'center',
  },
  card: {
    backgroundColor: '#FFFFFF',
    padding: 20,
    borderRadius: 12,
    width: '100%',
    alignItems: 'center',
    borderColor: '#E2E8F0',
    borderWidth: 1,
    marginBottom: 24,
  },
  label: {
    fontSize: 16,
    color: '#64748B',
    marginBottom: 8,
  },
  statusText: {
    fontSize: 18,
    fontWeight: '600',
  },
  success: {
    color: '#059669',
  },
  failure: {
    color: '#DC2626',
  },
  spinner: {
    marginTop: 8,
  },
  button: {
    backgroundColor: '#2563EB',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
