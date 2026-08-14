import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  View,
  SafeAreaView,
  StatusBar,
  TouchableOpacity,
  Text,
  Platform,
} from 'react-native';
import { StatusBar as ExpoStatusBar } from 'expo-status-bar';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { colors } from './src/theme/colors';
import { spacing, radius } from './src/theme/spacing';
import { typography } from './src/theme/typography';
import { AppHeader } from './src/components/AppHeader';
import { ScanScreen } from './src/screens/ScanScreen';
import { ReviewScreen } from './src/screens/ReviewScreen';
import { LibraryScreen } from './src/screens/LibraryScreen';
import { apiClient } from './src/api/client';
import { AnalyzeResponse } from './src/api/types';

type ScreenTab = 'scan' | 'review' | 'library';

export default function App() {
  const [currentTab, setCurrentTab] = useState<ScreenTab>('scan');
  const [activeScanResult, setActiveScanResult] = useState<{
    result: AnalyzeResponse;
    imageUri: string;
  } | null>(null);
  const [libraryCount, setLibraryCount] = useState<number>(0);

  // Fetch count of books in library
  const refreshLibraryCount = async () => {
    try {
      const data = await apiClient.getLibrary();
      setLibraryCount(data.count || (data.books ? data.books.length : 0));
    } catch {
      // Graceful fallback
    }
  };

  useEffect(() => {
    refreshLibraryCount();
  }, []);

  const handleScanComplete = (result: AnalyzeResponse, imageUri: string) => {
    setActiveScanResult({ result, imageUri });
    setCurrentTab('review');
  };

  const handleNavigateLibrary = () => {
    refreshLibraryCount();
    setCurrentTab('library');
  };

  const handleNavigateScan = () => {
    setActiveScanResult(null);
    setCurrentTab('scan');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ExpoStatusBar style="dark" />
      <View style={styles.container}>
        {/* Top App Bar */}
        <AppHeader
          title="Shelfie"
          onBack={currentTab === 'review' ? handleNavigateScan : undefined}
        />

        {/* Main Screen Content */}
        <View style={styles.screenContainer}>
          {currentTab === 'scan' ? (
            <ScanScreen
              onScanComplete={handleScanComplete}
              onNavigateLibrary={handleNavigateLibrary}
              libraryCount={libraryCount}
            />
          ) : currentTab === 'review' && activeScanResult ? (
            <ReviewScreen
              scanResult={activeScanResult.result}
              imageUri={activeScanResult.imageUri}
              onNavigateLibrary={handleNavigateLibrary}
              onScanAnother={handleNavigateScan}
            />
          ) : (
            <LibraryScreen onNavigateScan={handleNavigateScan} />
          )}
        </View>

        {/* Bottom Navigation Bar */}
        <View style={styles.bottomNav}>
          <View style={styles.bottomNavContent}>
            {/* Scan Tab */}
            <TouchableOpacity
              style={[
                styles.navButton,
                currentTab === 'scan' && styles.navButtonActive,
              ]}
              onPress={handleNavigateScan}
              accessibilityRole="tab"
              accessibilityState={{ selected: currentTab === 'scan' }}
              activeOpacity={0.8}
            >
              <MaterialCommunityIcons
                name="barcode-scan"
                size={22}
                color={currentTab === 'scan' ? colors.leatherGold : colors.textSecondary}
              />
              <Text
                style={[
                  typography.labelSmall,
                  styles.navLabel,
                  currentTab === 'scan' && styles.navLabelActive,
                ]}
              >
                Scan
              </Text>
            </TouchableOpacity>

            {/* In Review Flow Tab */}
            {activeScanResult ? (
              <TouchableOpacity
                style={[
                  styles.navButton,
                  currentTab === 'review' && styles.navButtonActive,
                ]}
                onPress={() => setCurrentTab('review')}
                accessibilityRole="tab"
                accessibilityState={{ selected: currentTab === 'review' }}
                activeOpacity={0.8}
              >
                <MaterialCommunityIcons
                  name="clipboard-text-outline"
                  size={22}
                  color={currentTab === 'review' ? colors.leatherGold : colors.textSecondary}
                />
                <Text
                  style={[
                    typography.labelSmall,
                    styles.navLabel,
                    currentTab === 'review' && styles.navLabelActive,
                  ]}
                >
                  Review
                </Text>
              </TouchableOpacity>
            ) : null}

            {/* Library Tab */}
            <TouchableOpacity
              style={[
                styles.navButton,
                currentTab === 'library' && styles.navButtonActive,
              ]}
              onPress={handleNavigateLibrary}
              accessibilityRole="tab"
              accessibilityState={{ selected: currentTab === 'library' }}
              activeOpacity={0.8}
            >
              <MaterialCommunityIcons
                name="book-open-page-variant"
                size={22}
                color={currentTab === 'library' ? colors.leatherGold : colors.textSecondary}
              />
              <Text
                style={[
                  typography.labelSmall,
                  styles.navLabel,
                  currentTab === 'library' && styles.navLabelActive,
                ]}
              >
                Library {libraryCount > 0 ? `(${libraryCount})` : ''}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
  },
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  screenContainer: {
    flex: 1,
  },
  bottomNav: {
    backgroundColor: colors.background,
    borderTopWidth: 1,
    borderTopColor: colors.borderLight,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
  },
  bottomNavContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    maxWidth: 600,
    width: '100%',
    alignSelf: 'center',
  },
  navButton: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 6,
    paddingHorizontal: spacing.xl,
    borderRadius: radius.lg, // 16px (rounded-2xl)
    minWidth: 100,
  },
  navButtonActive: {
    backgroundColor: colors.leather,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  navLabel: {
    color: colors.textSecondary,
    marginTop: 3,
  },
  navLabelActive: {
    color: colors.leatherGold,
    fontWeight: '700',
  },
});
