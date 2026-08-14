import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { MaterialCommunityIcons, Feather } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import { spacing, radius } from '../theme/spacing';
import { typography } from '../theme/typography';
import { PrimaryButton } from './PrimaryButton';

interface EmptyStateProps {
  title: string;
  description: string;
  actionTitle?: string;
  onAction?: () => void;
  iconName?: 'book-open-page-variant' | 'camera-outline' | 'magnify' | 'alert-circle-outline';
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  actionTitle,
  onAction,
  iconName = 'book-open-page-variant',
}) => {
  return (
    <View style={styles.container}>
      {/* Decorative Circular Framed Illustration */}
      <View style={styles.circleContainer}>
        <View style={styles.innerRingOuter} />
        <View style={styles.innerRingInner} />
        <MaterialCommunityIcons
          name={iconName}
          size={56}
          color={colors.textMuted}
          style={styles.icon}
        />
      </View>

      <Text style={[typography.headlineLarge, styles.title]}>{title}</Text>
      <Text style={[typography.bodyLarge, styles.description]}>{description}</Text>

      {actionTitle && onAction ? (
        <View style={styles.btnWrapper}>
          <PrimaryButton
            title={actionTitle}
            variant="leather"
            onPress={onAction}
            icon={<MaterialCommunityIcons name="barcode-scan" size={20} color={colors.leatherGold} />}
            style={styles.button}
          />
        </View>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: spacing.xxl,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'transparent',
    marginVertical: spacing.xl,
    width: '100%',
  },
  circleContainer: {
    width: 160,
    height: 160,
    borderRadius: 80,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.xl,
    position: 'relative',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  innerRingOuter: {
    position: 'absolute',
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 1,
    borderColor: colors.borderLight,
    opacity: 0.6,
  },
  innerRingInner: {
    position: 'absolute',
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 1,
    borderColor: colors.borderLight,
    opacity: 0.4,
  },
  icon: {
    zIndex: 2,
  },
  title: {
    textAlign: 'center',
    marginBottom: spacing.sm,
    color: colors.textPrimary,
  },
  description: {
    textAlign: 'center',
    color: colors.textSecondary,
    marginBottom: spacing.xl,
    maxWidth: 340,
  },
  btnWrapper: {
    width: '100%',
    maxWidth: 280,
  },
  button: {
    width: '100%',
  },
});
