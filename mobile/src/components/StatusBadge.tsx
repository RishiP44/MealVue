import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors } from '../theme/colors';
import { spacing, radius } from '../theme/spacing';
import { typography } from '../theme/typography';
import { ItemState } from '../api/types';

interface StatusBadgeProps {
  state: ItemState;
  confidence?: number | null;
  labelOverride?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  state,
  confidence,
  labelOverride,
}) => {
  const getBadgeConfig = () => {
    switch (state) {
      case 'matched':
        return {
          bg: colors.matched.bg,
          border: colors.matched.border,
          text: colors.matched.text,
          dotColor: colors.matched.solid,
          defaultLabel: confidence ? `Strong match · ${Math.round(confidence * 100)}%` : 'Strong match',
        };
      case 'needs_review':
        return {
          bg: colors.needsReview.bg,
          border: colors.needsReview.border,
          text: colors.needsReview.text,
          dotColor: colors.needsReview.solid,
          defaultLabel: confidence ? `Needs Review · ${Math.round(confidence * 100)}%` : 'Needs Review',
        };
      case 'unmatched':
        return {
          bg: colors.unmatched.bg,
          border: colors.unmatched.border,
          text: colors.unmatched.text,
          dotColor: colors.unmatched.text,
          defaultLabel: 'No match',
        };
      case 'unreadable':
        return {
          bg: colors.unreadable.bg,
          border: colors.unreadable.border,
          text: colors.unreadable.text,
          dotColor: colors.unreadable.text,
          defaultLabel: "Couldn't read spine",
        };
      case 'extraction_failed':
      default:
        return {
          bg: colors.failed.bg,
          border: colors.failed.border,
          text: colors.failed.text,
          dotColor: colors.failed.text,
          defaultLabel: 'Processing issue',
        };
    }
  };

  const config = getBadgeConfig();
  const label = labelOverride || config.defaultLabel;

  return (
    <View
      style={[
        styles.badge,
        {
          backgroundColor: config.bg,
          borderColor: config.border,
        },
      ]}
      accessibilityRole="text"
      accessibilityLabel={`Status: ${label}`}
    >
      <View style={[styles.dot, { backgroundColor: config.dotColor }]} />
      <Text style={[typography.labelSmall, { color: config.text }]}>
        {label}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: spacing.xs,
    borderRadius: radius.full,
    borderWidth: 1,
    gap: 6,
    alignSelf: 'flex-start',
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
});
