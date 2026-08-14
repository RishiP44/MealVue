import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  Image,
  ScrollView,
  Alert,
  TouchableOpacity,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import { spacing, radius } from '../theme/spacing';
import { typography } from '../theme/typography';
import { PrimaryButton } from '../components/PrimaryButton';
import { LoadingState } from '../components/LoadingState';
import { EmptyState } from '../components/EmptyState';
import { apiClient } from '../api/client';
import { AnalyzeResponse } from '../api/types';

interface ScanScreenProps {
  onScanComplete: (result: AnalyzeResponse, imageUri: string) => void;
  onNavigateLibrary: () => void;
  libraryCount: number;
}

export const ScanScreen: React.FC<ScanScreenProps> = ({
  onScanComplete,
  onNavigateLibrary,
  libraryCount,
}) => {
  const [selectedImageUri, setSelectedImageUri] = useState<string | null>(null);
  const [selectedMimeType, setSelectedMimeType] = useState<string>('image/jpeg');
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [noBooksWarning, setNoBooksWarning] = useState<boolean>(false);

  // Take photo with camera
  const handleTakePhoto = async () => {
    setErrorMessage(null);
    setNoBooksWarning(false);
    try {
      const permission = await ImagePicker.requestCameraPermissionsAsync();
      if (!permission.granted) {
        Alert.alert(
          'Camera Permission Required',
          'Please grant camera access to photograph your bookshelf, or choose an existing photo from your library instead.'
        );
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ['images'],
        quality: 0.9,
        allowsEditing: false,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];
        setSelectedImageUri(asset.uri);
        setSelectedMimeType(asset.mimeType || 'image/jpeg');
      }
    } catch (err: any) {
      setErrorMessage(`Could not access camera: ${err.message || 'Unknown error'}`);
    }
  };

  // Choose photo from photo library
  const handleChoosePhoto = async () => {
    setErrorMessage(null);
    setNoBooksWarning(false);
    try {
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permission.granted) {
        Alert.alert(
          'Photo Access Required',
          'Please grant photo library access to select a bookshelf photo.'
        );
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        quality: 0.9,
        allowsEditing: false,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];
        setSelectedImageUri(asset.uri);
        setSelectedMimeType(asset.mimeType || 'image/jpeg');
      }
    } catch (err: any) {
      setErrorMessage(`Could not open photo library: ${err.message || 'Unknown error'}`);
    }
  };

  // Execute bookshelf analysis
  const handleAnalyze = async () => {
    if (!selectedImageUri) return;
    setLoading(true);
    setErrorMessage(null);
    setNoBooksWarning(false);

    try {
      const res = await apiClient.analyzeShelf(
        selectedImageUri,
        selectedMimeType,
        'bookshelf.jpg'
      );

      if (res.status === 'no_books_detected' || (res.summary.detections === 0 && res.items.length === 0)) {
        setNoBooksWarning(true);
      } else {
        onScanComplete(res, selectedImageUri);
      }
    } catch (err: any) {
      setErrorMessage(
        err.message || "We couldn't finish analyzing this shelf. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedImageUri(null);
    setErrorMessage(null);
    setNoBooksWarning(false);
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
    >
      {/* Brand Hero */}
      <View style={styles.heroSection}>
        <Text style={[typography.headlineLarge, styles.heroTitle]}>
          Turn a shelf into your library.
        </Text>
        <Text style={[typography.bodyMedium, styles.heroSubtitle]}>
          For best results, keep book spines visible and the shelf well lit.
        </Text>
      </View>

      {/* Loading State */}
      {loading ? (
        <LoadingState
          title="Analyzing your bookshelf."
          subtitle="Finding books, reading spines, and matching your library."
        />
      ) : noBooksWarning ? (
        /* No Books Detected Dedicated State */
        <EmptyState
          iconName="camera-outline"
          title="No books detected"
          description="Try moving closer, improving the lighting, or keeping the bookshelf more front-facing."
          actionTitle="Choose Another Photo"
          onAction={handleReset}
        />
      ) : selectedImageUri ? (
        /* Image Preview & Confirmation State */
        <View style={styles.previewContainer}>
          <View style={styles.imageWrapper}>
            <Image
              source={{ uri: selectedImageUri }}
              style={styles.previewImage}
              resizeMode="contain"
            />
          </View>

          {errorMessage ? (
            <View style={styles.errorBox}>
              <Text style={[typography.bodyMedium, styles.errorTitle]}>Analysis Failed</Text>
              <Text style={[typography.bodySmall, styles.errorText]}>{errorMessage}</Text>
            </View>
          ) : null}

          <View style={styles.previewActions}>
            <PrimaryButton
              title="Analyze Shelf"
              variant="leather"
              onPress={handleAnalyze}
              icon={<MaterialCommunityIcons name="barcode-scan" size={22} color={colors.leatherGold} />}
              style={styles.mainActionBtn}
            />
            <PrimaryButton
              title="Choose another photo"
              variant="secondary"
              onPress={handleReset}
            />
          </View>
        </View>
      ) : (
        /* Initial Photo Selection State */
        <View style={styles.selectionContainer}>
          <View style={styles.actionButtons}>
            <PrimaryButton
              title="Take a photo"
              variant="leather"
              onPress={handleTakePhoto}
              icon={<Feather name="camera" size={20} color={colors.leatherGold} />}
              style={styles.buttonSpacing}
            />
            <PrimaryButton
              title="Choose from library"
              variant="secondary"
              onPress={handleChoosePhoto}
              icon={<Feather name="image" size={20} color={colors.textPrimary} />}
            />
          </View>

          {errorMessage ? (
            <View style={styles.errorBox}>
              <Text style={[typography.bodySmall, styles.errorText]}>{errorMessage}</Text>
            </View>
          ) : null}

          {/* Personal Library Shortcut Card */}
          <TouchableOpacity
            style={styles.libraryCard}
            onPress={onNavigateLibrary}
            activeOpacity={0.8}
          >
            <View style={styles.libCardLeft}>
              <View style={styles.libIconCircle}>
                <MaterialCommunityIcons name="book-open-page-variant" size={20} color={colors.textPrimary} />
              </View>
              <View style={styles.libTextColumn}>
                <Text style={[typography.bodyMedium, styles.libCardTitle]}>Personal Library</Text>
                <Text style={[typography.bodySmall, styles.libCardSubtitle]}>
                  {libraryCount} {libraryCount === 1 ? 'book' : 'books'} saved
                </Text>
              </View>
            </View>
            <Feather name="chevron-right" size={20} color={colors.border} />
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.lg,
    paddingBottom: spacing.huge,
    maxWidth: 600,
    width: '100%',
    alignSelf: 'center',
  },
  heroSection: {
    paddingTop: spacing.xxl,
    paddingBottom: spacing.xxl,
    alignItems: 'center',
    textAlign: 'center',
  },
  heroTitle: {
    textAlign: 'center',
    marginBottom: spacing.sm,
    color: colors.textPrimary,
    maxWidth: 380,
  },
  heroSubtitle: {
    textAlign: 'center',
    color: colors.textSecondary,
    maxWidth: 340,
  },
  selectionContainer: {
    width: '100%',
    maxWidth: 380,
    alignSelf: 'center',
  },
  actionButtons: {
    width: '100%',
    marginBottom: spacing.xxxl,
  },
  buttonSpacing: {
    marginBottom: spacing.md,
  },
  libraryCard: {
    backgroundColor: colors.surface,
    padding: spacing.lg,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 2,
  },
  libCardLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  libIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.surfaceContainer,
    borderWidth: 1,
    borderColor: colors.borderLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  libTextColumn: {},
  libCardTitle: {
    fontWeight: '600',
    color: colors.textPrimary,
  },
  libCardSubtitle: {
    color: colors.textSecondary,
    marginTop: 2,
  },
  previewContainer: {
    backgroundColor: colors.surface,
    padding: spacing.lg,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.borderLight,
    maxWidth: 480,
    width: '100%',
    alignSelf: 'center',
  },
  imageWrapper: {
    width: '100%',
    height: 340,
    backgroundColor: colors.surfaceContainer,
    borderRadius: radius.md,
    overflow: 'hidden',
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  previewImage: {
    width: '100%',
    height: '100%',
  },
  previewActions: {
    gap: spacing.sm,
  },
  mainActionBtn: {
    marginBottom: spacing.xs,
  },
  errorBox: {
    backgroundColor: colors.failed.bg,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.failed.border,
    marginBottom: spacing.lg,
  },
  errorTitle: {
    color: colors.failed.text,
    fontWeight: '700',
    marginBottom: 2,
  },
  errorText: {
    color: colors.failed.text,
  },
});
