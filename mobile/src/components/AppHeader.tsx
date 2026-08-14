import React from 'react';
import { StyleSheet, Text, View, TouchableOpacity } from 'react-native';
import { Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { typography } from '../theme/typography';

interface AppHeaderProps {
  title?: string;
  subtitle?: string;
  onBack?: () => void;
  rightElement?: React.ReactNode;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  title = 'Shelfie',
  subtitle,
  onBack,
  rightElement,
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.content}>
        {onBack ? (
          <TouchableOpacity
            style={styles.iconBtn}
            onPress={onBack}
            accessibilityRole="button"
            accessibilityLabel="Go back"
          >
            <Feather name="arrow-left" size={22} color={colors.textPrimary} />
          </TouchableOpacity>
        ) : (
          <View style={styles.iconPlaceholder} />
        )}

        <View style={styles.titleContainer}>
          <Text style={[typography.wordmark, styles.title]}>{title}</Text>
          {subtitle ? (
            <Text style={[typography.labelSmall, styles.subtitle]}>{subtitle}</Text>
          ) : null}
        </View>

        {rightElement ? (
          <View style={styles.right}>{rightElement}</View>
        ) : (
          <View style={styles.iconPlaceholder} />
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.background,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    maxWidth: 600,
    width: '100%',
    alignSelf: 'center',
    paddingHorizontal: spacing.lg,
    height: 48,
  },
  iconBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'transparent',
  },
  iconPlaceholder: {
    width: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  titleContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    color: colors.textPrimary,
    fontSize: 28,
  },
  subtitle: {
    color: colors.textSecondary,
    marginTop: -2,
  },
  right: {
    minWidth: 36,
    alignItems: 'flex-end',
  },
});
