import React from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
} from 'react-native';
import { Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import { spacing, radius } from '../theme/spacing';
import { typography } from '../theme/typography';
import { StatusBadge } from './StatusBadge';
import { PrimaryButton } from './PrimaryButton';
import { AnalysisItem, CatalogCandidate } from '../api/types';

export interface LocalItemState {
  item: AnalysisItem;
  isSelected: boolean;
  isConfirmed: boolean;
  isDiscarded: boolean;
  customTitle?: string | null;
  customAuthor?: string | null;
  selectedCandidate?: CatalogCandidate | null;
}

interface ResultCardProps {
  localState: LocalItemState;
  onToggleSelect: (itemId: string) => void;
  onConfirmSuggestion: (itemId: string, candidate: CatalogCandidate) => void;
  onSelectAlternative: (itemId: string, candidate: CatalogCandidate) => void;
  onOpenCorrection: (itemId: string) => void;
  onDiscard: (itemId: string) => void;
  onRestore: (itemId: string) => void;
}

export const ResultCard: React.FC<ResultCardProps> = ({
  localState,
  onToggleSelect,
  onConfirmSuggestion,
  onSelectAlternative,
  onOpenCorrection,
  onDiscard,
  onRestore,
}) => {
  const { item, isSelected, isConfirmed, isDiscarded, customTitle, customAuthor, selectedCandidate } = localState;

  if (isDiscarded) {
    return (
      <View style={[styles.card, styles.discardedCard]}>
        <View style={styles.discardedRow}>
          <Text style={[typography.bodySmall, styles.discardedText]}>
            [{item.item_id}] Discarded book
          </Text>
          <TouchableOpacity onPress={() => onRestore(item.item_id)}>
            <Text style={styles.restoreText}>Restore</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // Determine active candidate
  const activeCandidate = selectedCandidate || item.match?.best_candidate || null;
  const confidence = item.match?.confidence || null;
  const isCustomManual = Boolean(customTitle && !activeCandidate);

  // Render Card Content by State
  const renderCardBody = () => {
    switch (item.state) {
      case 'matched':
        return (
          <View style={styles.bodyContainer}>
            {/* Green accent stripe on left */}
            <View style={styles.successStripe} />

            <View style={styles.matchedContent}>
              <View style={styles.matchedMain}>
                <View style={styles.badgeRow}>
                  <StatusBadge state="matched" confidence={confidence} />
                </View>

                <Text style={[typography.headlineSmall, styles.bookTitle]} numberOfLines={2}>
                  {activeCandidate?.title || item.extraction.title || 'Untitled'}
                </Text>
                <Text style={[typography.bodySmall, styles.bookAuthor]} numberOfLines={1}>
                  {activeCandidate?.author || item.extraction.author || 'Unknown Author'}
                </Text>
                {activeCandidate?.edition ? (
                  <Text style={[typography.labelSmall, styles.editionText]}>
                    Edition: {activeCandidate.edition}
                  </Text>
                ) : null}
              </View>

              {/* Selection Checkbox */}
              <TouchableOpacity
                style={[styles.checkbox, isSelected && styles.checkboxSelected]}
                onPress={() => onToggleSelect(item.item_id)}
                accessibilityRole="checkbox"
                accessibilityState={{ checked: isSelected }}
              >
                {isSelected ? (
                  <Feather name="check" size={16} color={colors.textInverse} />
                ) : null}
              </TouchableOpacity>
            </View>
          </View>
        );

      case 'needs_review':
        return (
          <View style={styles.bodyContainer}>
            <View style={styles.headerRow}>
              <StatusBadge
                state={isConfirmed ? 'matched' : 'needs_review'}
                confidence={confidence}
                labelOverride={isConfirmed ? 'Confirmed ✓' : undefined}
              />
              <TouchableOpacity
                style={[styles.checkbox, isSelected && styles.checkboxSelected]}
                onPress={() => onToggleSelect(item.item_id)}
                accessibilityRole="checkbox"
                accessibilityState={{ checked: isSelected }}
              >
                {isSelected ? (
                  <Feather name="check" size={16} color={colors.textInverse} />
                ) : null}
              </TouchableOpacity>
            </View>

            {/* Comparison Area: Detected OCR vs Suggested Match */}
            <View style={styles.comparisonGrid}>
              {/* Detected OCR (Dashed Box) */}
              <View style={styles.ocrBox}>
                <Text style={[typography.labelSmall, styles.boxHeader]}>DETECTED OCR</Text>
                <Text style={[typography.bodyMedium, styles.ocrText]} numberOfLines={3}>
                  "{item.extraction.title || '(No title recognized)'}
                  {item.extraction.author ? ` - ${item.extraction.author}` : ''}"
                </Text>
              </View>

              {/* Suggested Match or Custom Manual Confirmation */}
              {isCustomManual ? (
                <View style={styles.suggestedBox}>
                  <Text style={[typography.labelSmall, styles.boxHeader]}>MANUAL CONFIRMATION</Text>
                  <Text style={[typography.headlineSmall, styles.bookTitle]} numberOfLines={2}>{customTitle}</Text>
                  <Text style={[typography.bodySmall, styles.bookAuthor]}>by {customAuthor || 'Unknown'}</Text>
                </View>
              ) : activeCandidate ? (
                <View style={styles.suggestedBox}>
                  <Text style={[typography.labelSmall, styles.boxHeaderHighlight]}>SUGGESTED MATCH</Text>
                  <Text style={[typography.headlineSmall, styles.bookTitle]} numberOfLines={2}>{activeCandidate.title}</Text>
                  <Text style={[typography.bodySmall, styles.bookAuthor]}>by {activeCandidate.author}</Text>
                  {activeCandidate.edition ? (
                    <Text style={[typography.labelSmall, styles.editionText]}>
                      Edition: {activeCandidate.edition}
                    </Text>
                  ) : null}
                </View>
              ) : null}
            </View>

            {/* Alternative Possibilities Chips */}
            {item.match?.alternatives && item.match.alternatives.length > 0 && !isConfirmed ? (
              <View style={styles.alternativesBox}>
                <Text style={[typography.labelSmall, styles.altHeader]}>OTHER POSSIBILITIES:</Text>
                <View style={styles.altChipContainer}>
                  {item.match.alternatives.map((alt) => (
                    <TouchableOpacity
                      key={alt.catalog_id}
                      style={[
                        styles.altChip,
                        activeCandidate?.catalog_id === alt.catalog_id && styles.altChipActive,
                      ]}
                      onPress={() => onSelectAlternative(item.item_id, alt)}
                    >
                      <Text style={[typography.labelSmall, styles.altChipText]} numberOfLines={1}>
                        {alt.title}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            ) : null}

            {/* Action Buttons Row */}
            <View style={styles.btnRow}>
              <PrimaryButton
                title="Discard"
                variant="ghost"
                onPress={() => onDiscard(item.item_id)}
                style={styles.actionBtnGhost}
              />
              <PrimaryButton
                title="Correct"
                variant="secondary"
                onPress={() => onOpenCorrection(item.item_id)}
                style={styles.actionBtnSecondary}
              />
              {activeCandidate && !isConfirmed ? (
                <PrimaryButton
                  title="Confirm"
                  variant="leather"
                  onPress={() => onConfirmSuggestion(item.item_id, activeCandidate)}
                  style={styles.actionBtnPrimary}
                />
              ) : null}
            </View>
          </View>
        );

      case 'unmatched':
        return (
          <View style={styles.bodyContainer}>
            <View style={styles.headerRow}>
              <StatusBadge state="unmatched" />
              {isCustomManual ? (
                <TouchableOpacity
                  style={[styles.checkbox, isSelected && styles.checkboxSelected]}
                  onPress={() => onToggleSelect(item.item_id)}
                >
                  {isSelected ? <Feather name="check" size={16} color={colors.textInverse} /> : null}
                </TouchableOpacity>
              ) : null}
            </View>

            {isCustomManual ? (
              <View style={styles.suggestedBox}>
                <Text style={[typography.labelSmall, styles.boxHeader]}>MANUAL CONFIRMATION</Text>
                <Text style={[typography.headlineSmall, styles.bookTitle]}>{customTitle}</Text>
                <Text style={[typography.bodySmall, styles.bookAuthor]}>by {customAuthor || 'Unknown'}</Text>
              </View>
            ) : (
              <View style={styles.unmatchedBox}>
                <Text style={[typography.bodySmall, styles.unmatchedExplain]}>
                  We couldn't confidently match this spine to our canonical catalog.
                </Text>
                <View style={styles.ocrBox}>
                  <Text style={[typography.labelSmall, styles.boxHeader]}>DETECTED OCR</Text>
                  <Text style={[typography.bodyMedium, styles.ocrText]}>
                    "{item.extraction.title || '(No title recognized)'}
                    {item.extraction.author ? ` - ${item.extraction.author}` : ''}"
                  </Text>
                </View>
              </View>
            )}

            <View style={styles.btnRow}>
              <PrimaryButton
                title="Discard"
                variant="ghost"
                onPress={() => onDiscard(item.item_id)}
                style={styles.actionBtnGhost}
              />
              <PrimaryButton
                title="Correct / Search"
                variant="secondary"
                onPress={() => onOpenCorrection(item.item_id)}
                style={styles.actionBtnSecondary}
              />
            </View>
          </View>
        );

      case 'unreadable':
        return (
          <View style={styles.bodyContainer}>
            <View style={styles.headerRow}>
              <StatusBadge state="unreadable" />
              {isCustomManual ? (
                <TouchableOpacity
                  style={[styles.checkbox, isSelected && styles.checkboxSelected]}
                  onPress={() => onToggleSelect(item.item_id)}
                >
                  {isSelected ? <Feather name="check" size={16} color={colors.textInverse} /> : null}
                </TouchableOpacity>
              ) : null}
            </View>

            {isCustomManual ? (
              <View style={styles.suggestedBox}>
                <Text style={[typography.labelSmall, styles.boxHeader]}>MANUAL ENTRY</Text>
                <Text style={[typography.headlineSmall, styles.bookTitle]}>{customTitle}</Text>
                <Text style={[typography.bodySmall, styles.bookAuthor]}>by {customAuthor || 'Unknown'}</Text>
              </View>
            ) : (
              <View style={styles.unreadableBox}>
                <Text style={[typography.headlineSmall, styles.unreadableTitle]}>Couldn't read this spine</Text>
                <Text style={[typography.bodySmall, styles.unreadableDesc]}>
                  A book was detected on the shelf, but the title and author text were illegible.
                </Text>
              </View>
            )}

            <View style={styles.btnRow}>
              <PrimaryButton
                title="Discard"
                variant="ghost"
                onPress={() => onDiscard(item.item_id)}
                style={styles.actionBtnGhost}
              />
              <PrimaryButton
                title="Enter Manually"
                variant="secondary"
                onPress={() => onOpenCorrection(item.item_id)}
                style={styles.actionBtnSecondary}
              />
            </View>
          </View>
        );

      case 'extraction_failed':
      default:
        return (
          <View style={styles.bodyContainer}>
            <StatusBadge state="extraction_failed" />
            <View style={styles.failedBox}>
              <Text style={[typography.headlineSmall, styles.failedTitle]}>Couldn't process this book</Text>
              <Text style={[typography.bodySmall, styles.failedDesc]}>
                A temporary network issue occurred during spine reading.
              </Text>
            </View>
            <View style={styles.btnRow}>
              <PrimaryButton
                title="Discard"
                variant="ghost"
                onPress={() => onDiscard(item.item_id)}
                style={styles.actionBtnGhost}
              />
            </View>
          </View>
        );
    }
  };

  return (
    <View style={[styles.card, isSelected && styles.cardSelected]}>
      {renderCardBody()}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.borderLight,
    marginBottom: spacing.md,
    position: 'relative',
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
  },
  cardSelected: {
    borderColor: colors.border,
    backgroundColor: colors.surfaceWhite,
  },
  discardedCard: {
    backgroundColor: colors.surfaceContainer,
    borderColor: colors.borderLight,
    padding: spacing.md,
    opacity: 0.7,
  },
  discardedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  discardedText: {
    color: colors.textMuted,
  },
  restoreText: {
    color: colors.leather,
    fontWeight: '700',
    fontSize: 13,
  },
  bodyContainer: {
    width: '100%',
  },
  successStripe: {
    position: 'absolute',
    left: -spacing.lg,
    top: -spacing.lg,
    bottom: -spacing.lg,
    width: 4,
    backgroundColor: colors.matched.solid,
  },
  matchedContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  matchedMain: {
    flex: 1,
    marginRight: spacing.md,
  },
  badgeRow: {
    marginBottom: spacing.xs,
  },
  bookTitle: {
    color: colors.textPrimary,
  },
  bookAuthor: {
    color: colors.textSecondary,
    marginTop: 2,
  },
  editionText: {
    color: colors.textMuted,
    marginTop: 4,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  checkbox: {
    width: 28,
    height: 28,
    borderRadius: radius.sm,
    borderWidth: 1.5,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surface,
  },
  checkboxSelected: {
    backgroundColor: colors.matched.solid,
    borderColor: colors.matched.solid,
  },
  comparisonGrid: {
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  ocrBox: {
    backgroundColor: colors.background,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    borderStyle: 'dashed',
  },
  boxHeader: {
    color: colors.textSecondary,
    marginBottom: 4,
  },
  boxHeaderHighlight: {
    color: colors.needsReview.text,
    marginBottom: 4,
  },
  ocrText: {
    fontStyle: 'italic',
    color: colors.textPrimary,
  },
  suggestedBox: {
    backgroundColor: colors.surfaceContainer,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  alternativesBox: {
    marginVertical: spacing.xs,
  },
  altHeader: {
    color: colors.textSecondary,
    marginBottom: 6,
  },
  altChipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
  },
  altChip: {
    backgroundColor: colors.surfaceContainer,
    borderWidth: 1,
    borderColor: colors.borderLight,
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: spacing.xs,
    borderRadius: radius.full,
    maxWidth: '100%',
  },
  altChipActive: {
    backgroundColor: colors.needsReview.bg,
    borderColor: colors.needsReview.border,
  },
  altChipText: {
    color: colors.textPrimary,
  },
  unmatchedBox: {
    marginBottom: spacing.sm,
  },
  unmatchedExplain: {
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  unreadableBox: {
    marginBottom: spacing.sm,
  },
  unreadableTitle: {
    color: colors.textPrimary,
    marginBottom: 2,
  },
  unreadableDesc: {
    color: colors.textSecondary,
  },
  failedBox: {
    marginVertical: spacing.md,
  },
  failedTitle: {
    color: colors.failed.text,
    marginBottom: 2,
  },
  failedDesc: {
    color: colors.textSecondary,
  },
  btnRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: spacing.sm,
    marginTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.borderLight,
    paddingTop: spacing.sm,
  },
  actionBtnGhost: {
    minHeight: 38,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  actionBtnSecondary: {
    minHeight: 38,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  actionBtnPrimary: {
    minHeight: 38,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.xs,
  },
});
