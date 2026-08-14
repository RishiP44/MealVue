import { TextStyle, Platform } from 'react-native';
import { colors } from './colors';

const SERIF_FONT = Platform.select({
  ios: 'Georgia',
  android: 'serif',
  default: 'Georgia, serif',
});

const SANS_FONT = Platform.select({
  ios: 'System',
  android: 'sans-serif',
  default: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
});

export const typography: Record<string, TextStyle> = {
  wordmark: {
    fontFamily: SERIF_FONT,
    fontSize: 32,
    fontWeight: '800',
    color: colors.textPrimary,
    letterSpacing: -0.5,
  },
  displayLarge: {
    fontFamily: SERIF_FONT,
    fontSize: 32,
    fontWeight: '800',
    color: colors.textPrimary,
    letterSpacing: -0.3,
    lineHeight: 40,
  },
  headlineLarge: {
    fontFamily: SERIF_FONT,
    fontSize: 28,
    fontWeight: '800',
    color: colors.textPrimary,
    lineHeight: 36,
  },
  headlineSmall: {
    fontFamily: SERIF_FONT,
    fontSize: 20,
    fontWeight: '700',
    color: colors.textPrimary,
    lineHeight: 28,
  },
  bodyLarge: {
    fontFamily: SANS_FONT,
    fontSize: 18,
    color: colors.textSecondary,
    lineHeight: 28,
  },
  bodyMedium: {
    fontFamily: SANS_FONT,
    fontSize: 16,
    color: colors.textPrimary,
    lineHeight: 24,
  },
  bodySmall: {
    fontFamily: SANS_FONT,
    fontSize: 14,
    color: colors.textSecondary,
    lineHeight: 20,
  },
  labelMedium: {
    fontFamily: SANS_FONT,
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.6,
    textTransform: 'uppercase',
    color: colors.textSecondary,
  },
  labelSmall: {
    fontFamily: SANS_FONT,
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
};
