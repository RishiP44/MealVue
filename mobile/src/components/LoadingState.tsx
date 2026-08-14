import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, ActivityIndicator } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import { spacing, radius } from '../theme/spacing';
import { typography } from '../theme/typography';

interface LoadingStateProps {
  title?: string;
  subtitle?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  title = 'Analyzing your bookshelf.',
  subtitle = 'Finding books, reading spines, and matching your library.',
}) => {
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSeconds((s) => s + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <View style={styles.container}>
      <View style={styles.textSection}>
        <Text style={[typography.headlineLarge, styles.title]}>{title}</Text>
        <Text style={[typography.bodyLarge, styles.subtitle]}>{subtitle}</Text>
      </View>

      {/* Scanning Visual Container */}
      <View style={styles.cardContainer}>
        <View style={styles.iconCircle}>
          <MaterialCommunityIcons name="barcode-scan" size={40} color={colors.leather} />
        </View>

        <ActivityIndicator size="large" color={colors.leather} style={styles.spinner} />

        <View style={styles.timerBadge}>
          <Text style={[typography.labelMedium, styles.timerText]}>
            Processing · {elapsedSeconds}s elapsed
          </Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingVertical: spacing.xl,
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
  },
  textSection: {
    alignItems: 'center',
    marginBottom: spacing.xxl,
    maxWidth: 420,
  },
  title: {
    textAlign: 'center',
    marginBottom: spacing.xs,
    color: colors.textPrimary,
  },
  subtitle: {
    textAlign: 'center',
    color: colors.textSecondary,
  },
  cardContainer: {
    width: '100%',
    maxWidth: 320,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.xxl,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 3,
  },
  iconCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: colors.surfaceContainer,
    borderWidth: 1,
    borderColor: colors.borderLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.xl,
  },
  spinner: {
    marginBottom: spacing.lg,
  },
  timerBadge: {
    backgroundColor: colors.surfaceContainer,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
    borderRadius: radius.full,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  timerText: {
    color: colors.textSecondary,
  },
});
