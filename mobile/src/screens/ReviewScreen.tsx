import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { Feather, MaterialCommunityIcons, MaterialIcons } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import { spacing, radius } from '../theme/spacing';
import { typography } from '../theme/typography';
import { ResultCard, LocalItemState } from '../components/ResultCard';
import { PrimaryButton } from '../components/PrimaryButton';
import { CorrectionModal } from '../components/CorrectionModal';
import { apiClient } from '../api/client';
import {
  AnalyzeResponse,
  CatalogCandidate,
  LibraryAddRequestItem,
} from '../api/types';

interface ReviewScreenProps {
  scanResult: AnalyzeResponse;
  imageUri: string;
  onNavigateLibrary: () => void;
  onScanAnother: () => void;
}

export const ReviewScreen: React.FC<ReviewScreenProps> = ({
  scanResult,
  imageUri,
  onNavigateLibrary,
  onScanAnother,
}) => {
  // Local transient review items
  const [itemsState, setItemsState] = useState<Record<string, LocalItemState>>(() => {
    const map: Record<string, LocalItemState> = {};
    for (const item of scanResult.items) {
      // Pre-select high-confidence matched items by default (NOT auto-persisted)
      const isAutoSelected = item.state === 'matched';
      map[item.item_id] = {
        item,
        isSelected: isAutoSelected,
        isConfirmed: isAutoSelected,
        isDiscarded: false,
        customTitle: null,
        customAuthor: null,
        selectedCandidate: item.match?.best_candidate || null,
      };
    }
    return map;
  });

  // Collapsible section visibility states
  const [readyExpanded, setReadyExpanded] = useState<boolean>(true);
  const [reviewExpanded, setReviewExpanded] = useState<boolean>(true);
  const [unmatchedExpanded, setUnmatchedExpanded] = useState<boolean>(true);
  const [unreadableExpanded, setUnreadableExpanded] = useState<boolean>(true);
  const [failedExpanded, setFailedExpanded] = useState<boolean>(true);

  const [activeCorrectionId, setActiveCorrectionId] = useState<string | null>(null);
  const [savingBooks, setSavingBooks] = useState<boolean>(false);
  const [savedSummary, setSavedSummary] = useState<{
    added: number;
    duplicates: number;
  } | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Toggle item selection
  const handleToggleSelect = (itemId: string) => {
    setItemsState((prev) => {
      const curr = prev[itemId];
      if (!curr) return prev;
      return {
        ...prev,
        [itemId]: {
          ...curr,
          isSelected: !curr.isSelected,
        },
      };
    });
  };

  // Confirm suggested candidate
  const handleConfirmSuggestion = (itemId: string, candidate: CatalogCandidate) => {
    setItemsState((prev) => {
      const curr = prev[itemId];
      if (!curr) return prev;
      return {
        ...prev,
        [itemId]: {
          ...curr,
          isConfirmed: true,
          isSelected: true,
          selectedCandidate: candidate,
        },
      };
    });
  };

  // Switch to an alternative candidate chip
  const handleSelectAlternative = (itemId: string, candidate: CatalogCandidate) => {
    setItemsState((prev) => {
      const curr = prev[itemId];
      if (!curr) return prev;
      return {
        ...prev,
        [itemId]: {
          ...curr,
          selectedCandidate: candidate,
          isConfirmed: true,
          isSelected: true,
        },
      };
    });
  };

  // Discard item
  const handleDiscard = (itemId: string) => {
    setItemsState((prev) => {
      const curr = prev[itemId];
      if (!curr) return prev;
      return {
        ...prev,
        [itemId]: {
          ...curr,
          isDiscarded: true,
          isSelected: false,
        },
      };
    });
  };

  // Restore discarded item
  const handleRestore = (itemId: string) => {
    setItemsState((prev) => {
      const curr = prev[itemId];
      if (!curr) return prev;
      return {
        ...prev,
        [itemId]: {
          ...curr,
          isDiscarded: false,
        },
      };
    });
  };

  // Confirm canonical match from modal
  const handleModalConfirmCanonical = (candidate: CatalogCandidate, confidence: number) => {
    if (!activeCorrectionId) return;
    setItemsState((prev) => {
      const curr = prev[activeCorrectionId];
      if (!curr) return prev;
      return {
        ...prev,
        [activeCorrectionId]: {
          ...curr,
          isConfirmed: true,
          isSelected: true,
          selectedCandidate: candidate,
          customTitle: null,
          customAuthor: null,
        },
      };
    });
    setActiveCorrectionId(null);
  };

  // Confirm manual freeform title/author from modal
  const handleModalConfirmManual = (title: string, author: string) => {
    if (!activeCorrectionId) return;
    setItemsState((prev) => {
      const curr = prev[activeCorrectionId];
      if (!curr) return prev;
      return {
        ...prev,
        [activeCorrectionId]: {
          ...curr,
          isConfirmed: true,
          isSelected: true,
          customTitle: title,
          customAuthor: author,
          selectedCandidate: null,
        },
      };
    });
    setActiveCorrectionId(null);
  };

  // Calculate selected count
  const allStates = Object.values(itemsState);
  const activeStates = allStates.filter((s) => !s.isDiscarded);
  const selectedStates = activeStates.filter((s) => s.isSelected);
  const selectedCount = selectedStates.length;

  // Persist selected books to Library
  const handleAddSelectedToLibrary = async () => {
    if (selectedCount === 0) return;
    setSavingBooks(true);
    setSaveError(null);

    const payload: LibraryAddRequestItem[] = [];

    for (const state of selectedStates) {
      if (state.selectedCandidate) {
        // Catalog-backed candidate
        payload.push({
          catalog_id: state.selectedCandidate.catalog_id,
          confirmed_title: state.selectedCandidate.title,
          confirmed_author: state.selectedCandidate.author,
          edition: state.selectedCandidate.edition,
          source_match_confidence: state.item.match?.confidence || null,
        });
      } else if (state.customTitle) {
        // Freeform manual addition
        payload.push({
          catalog_id: null,
          confirmed_title: state.customTitle,
          confirmed_author: state.customAuthor || null,
          edition: null,
          source_match_confidence: null,
        });
      } else if (state.item.extraction.title) {
        // Fallback to raw extracted title if explicitly selected
        payload.push({
          catalog_id: null,
          confirmed_title: state.item.extraction.title,
          confirmed_author: state.item.extraction.author || null,
          edition: null,
          source_match_confidence: null,
        });
      }
    }

    try {
      const res = await apiClient.addBooks(payload);
      setSavedSummary({
        added: res.added_count,
        duplicates: res.duplicate_count,
      });
    } catch (err: any) {
      setSaveError(err.message || 'Failed to save books to library.');
    } finally {
      setSavingBooks(false);
    }
  };

  // Group items
  const readyGroup = activeStates.filter(
    (s) => s.item.state === 'matched' || s.isConfirmed || Boolean(s.customTitle)
  );
  const needsReviewGroup = activeStates.filter(
    (s) => s.item.state === 'needs_review' && !s.isConfirmed && !s.customTitle
  );
  const unmatchedGroup = activeStates.filter(
    (s) => s.item.state === 'unmatched' && !s.isConfirmed && !s.customTitle
  );
  const unreadableGroup = activeStates.filter(
    (s) => s.item.state === 'unreadable' && !s.isConfirmed && !s.customTitle
  );
  const failedGroup = activeStates.filter(
    (s) => s.item.state === 'extraction_failed' && !s.isConfirmed && !s.customTitle
  );

  const activeItemForCorrection = activeCorrectionId ? itemsState[activeCorrectionId] : null;

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={[typography.headlineLarge, styles.headerTitle]}>Shelf results</Text>
        </View>

        {/* Success Confirmation Card */}
        {savedSummary ? (
          <View style={styles.successBanner}>
            <View style={styles.successIconCircle}>
              <Feather name="check" size={24} color={colors.textInverse} />
            </View>
            <Text style={[typography.headlineSmall, styles.successTitle]}>
              {savedSummary.added} {savedSummary.added === 1 ? 'book' : 'books'} added to library
            </Text>
            {savedSummary.duplicates > 0 ? (
              <Text style={[typography.bodySmall, styles.dupNote]}>
                ({savedSummary.duplicates} already existed in your collection)
              </Text>
            ) : null}
            <View style={styles.successActions}>
              <PrimaryButton
                title="View My Library"
                variant="leather"
                onPress={onNavigateLibrary}
                style={styles.successBtn}
              />
              <PrimaryButton
                title="Scan Another Shelf"
                variant="secondary"
                onPress={onScanAnother}
                style={styles.successBtn}
              />
            </View>
          </View>
        ) : null}

        {/* Summary Description Card */}
        <View style={styles.summaryCard}>
          <Text style={[typography.bodyLarge, styles.summaryText]}>
            {scanResult.summary.detections} {scanResult.summary.detections === 1 ? 'book' : 'books'} found:{' '}
            {scanResult.summary.matched > 0 && (
              <Text style={styles.highlightMatched}>{scanResult.summary.matched} Ready to add, </Text>
            )}
            {scanResult.summary.needs_review > 0 && (
              <Text style={styles.highlightReview}>{scanResult.summary.needs_review} Need review, </Text>
            )}
            {scanResult.summary.unmatched > 0 && (
              <Text style={styles.highlightUnmatched}>{scanResult.summary.unmatched} No match, </Text>
            )}
            {scanResult.summary.unreadable > 0 && (
              <Text style={styles.highlightUnreadable}>{scanResult.summary.unreadable} Couldn't read.</Text>
            )}
          </Text>
        </View>

        {saveError ? (
          <View style={styles.saveErrorBox}>
            <Text style={styles.saveErrorText}>{saveError}</Text>
          </View>
        ) : null}

        {/* Group 1: READY TO ADD */}
        {readyGroup.length > 0 ? (
          <View style={styles.groupSection}>
            <TouchableOpacity
              style={styles.groupHeaderRow}
              onPress={() => setReadyExpanded(!readyExpanded)}
              activeOpacity={0.7}
            >
              <View style={styles.groupHeaderLeft}>
                <Feather name="check-circle" size={18} color={colors.matched.text} />
                <Text style={[typography.headlineSmall, styles.groupTitle]}>READY TO ADD</Text>
                <View style={styles.countBadge}>
                  <Text style={styles.countBadgeText}>{readyGroup.length}</Text>
                </View>
              </View>
              <Feather
                name={readyExpanded ? 'chevron-up' : 'chevron-down'}
                size={20}
                color={colors.textSecondary}
              />
            </TouchableOpacity>

            {readyExpanded ? (
              <View style={styles.cardsContainer}>
                {readyGroup.map((s) => (
                  <ResultCard
                    key={s.item.item_id}
                    localState={s}
                    onToggleSelect={handleToggleSelect}
                    onConfirmSuggestion={handleConfirmSuggestion}
                    onSelectAlternative={handleSelectAlternative}
                    onOpenCorrection={(id) => setActiveCorrectionId(id)}
                    onDiscard={handleDiscard}
                    onRestore={handleRestore}
                  />
                ))}
              </View>
            ) : null}
          </View>
        ) : null}

        {/* Group 2: NEEDS REVIEW */}
        {needsReviewGroup.length > 0 ? (
          <View style={styles.groupSection}>
            <TouchableOpacity
              style={styles.groupHeaderRow}
              onPress={() => setReviewExpanded(!reviewExpanded)}
              activeOpacity={0.7}
            >
              <View style={styles.groupHeaderLeft}>
                <Feather name="help-circle" size={18} color={colors.needsReview.text} />
                <Text style={[typography.headlineSmall, styles.groupTitleReview]}>NEEDS REVIEW</Text>
                <View style={styles.countBadge}>
                  <Text style={styles.countBadgeText}>{needsReviewGroup.length}</Text>
                </View>
              </View>
              <Feather
                name={reviewExpanded ? 'chevron-up' : 'chevron-down'}
                size={20}
                color={colors.textSecondary}
              />
            </TouchableOpacity>

            {reviewExpanded ? (
              <View style={styles.cardsContainer}>
                {needsReviewGroup.map((s) => (
                  <ResultCard
                    key={s.item.item_id}
                    localState={s}
                    onToggleSelect={handleToggleSelect}
                    onConfirmSuggestion={handleConfirmSuggestion}
                    onSelectAlternative={handleSelectAlternative}
                    onOpenCorrection={(id) => setActiveCorrectionId(id)}
                    onDiscard={handleDiscard}
                    onRestore={handleRestore}
                  />
                ))}
              </View>
            ) : null}
          </View>
        ) : null}

        {/* Group 3: UNMATCHED / NO MATCH */}
        {unmatchedGroup.length > 0 ? (
          <View style={styles.groupSection}>
            <TouchableOpacity
              style={styles.groupHeaderRow}
              onPress={() => setUnmatchedExpanded(!unmatchedExpanded)}
              activeOpacity={0.7}
            >
              <View style={styles.groupHeaderLeft}>
                <Feather name="alert-circle" size={18} color={colors.textSecondary} />
                <Text style={[typography.headlineSmall, styles.groupTitle]}>NO MATCH</Text>
                <View style={styles.countBadgeSecondary}>
                  <Text style={styles.countBadgeTextSec}>{unmatchedGroup.length}</Text>
                </View>
              </View>
              <Feather
                name={unmatchedExpanded ? 'chevron-up' : 'chevron-down'}
                size={20}
                color={colors.textSecondary}
              />
            </TouchableOpacity>

            {unmatchedExpanded ? (
              <View style={styles.cardsContainer}>
                {unmatchedGroup.map((s) => (
                  <ResultCard
                    key={s.item.item_id}
                    localState={s}
                    onToggleSelect={handleToggleSelect}
                    onConfirmSuggestion={handleConfirmSuggestion}
                    onSelectAlternative={handleSelectAlternative}
                    onOpenCorrection={(id) => setActiveCorrectionId(id)}
                    onDiscard={handleDiscard}
                    onRestore={handleRestore}
                  />
                ))}
              </View>
            ) : null}
          </View>
        ) : null}

        {/* Group 4: COULDN'T READ */}
        {unreadableGroup.length > 0 ? (
          <View style={styles.groupSection}>
            <TouchableOpacity
              style={styles.groupHeaderRow}
              onPress={() => setUnreadableExpanded(!unreadableExpanded)}
              activeOpacity={0.7}
            >
              <View style={styles.groupHeaderLeft}>
                <Feather name="eye-off" size={18} color={colors.textMuted} />
                <Text style={[typography.headlineSmall, styles.groupTitle]}>COULDN'T READ</Text>
                <View style={styles.countBadgeSecondary}>
                  <Text style={styles.countBadgeTextSec}>{unreadableGroup.length}</Text>
                </View>
              </View>
              <Feather
                name={unreadableExpanded ? 'chevron-up' : 'chevron-down'}
                size={20}
                color={colors.textSecondary}
              />
            </TouchableOpacity>

            {unreadableExpanded ? (
              <View style={styles.cardsContainer}>
                {unreadableGroup.map((s) => (
                  <ResultCard
                    key={s.item.item_id}
                    localState={s}
                    onToggleSelect={handleToggleSelect}
                    onConfirmSuggestion={handleConfirmSuggestion}
                    onSelectAlternative={handleSelectAlternative}
                    onOpenCorrection={(id) => setActiveCorrectionId(id)}
                    onDiscard={handleDiscard}
                    onRestore={handleRestore}
                  />
                ))}
              </View>
            ) : null}
          </View>
        ) : null}

        {/* Group 5: PROCESSING ISSUES */}
        {failedGroup.length > 0 ? (
          <View style={styles.groupSection}>
            <TouchableOpacity
              style={styles.groupHeaderRow}
              onPress={() => setFailedExpanded(!failedExpanded)}
              activeOpacity={0.7}
            >
              <View style={styles.groupHeaderLeft}>
                <Feather name="slash" size={18} color={colors.failed.text} />
                <Text style={[typography.headlineSmall, styles.groupTitleFailed]}>PROCESSING ISSUES</Text>
                <View style={styles.countBadgeSecondary}>
                  <Text style={styles.countBadgeTextSec}>{failedGroup.length}</Text>
                </View>
              </View>
              <Feather
                name={failedExpanded ? 'chevron-up' : 'chevron-down'}
                size={20}
                color={colors.textSecondary}
              />
            </TouchableOpacity>

            {failedExpanded ? (
              <View style={styles.cardsContainer}>
                {failedGroup.map((s) => (
                  <ResultCard
                    key={s.item.item_id}
                    localState={s}
                    onToggleSelect={handleToggleSelect}
                    onConfirmSuggestion={handleConfirmSuggestion}
                    onSelectAlternative={handleSelectAlternative}
                    onOpenCorrection={(id) => setActiveCorrectionId(id)}
                    onDiscard={handleDiscard}
                    onRestore={handleRestore}
                  />
                ))}
              </View>
            ) : null}
          </View>
        ) : null}
      </ScrollView>

      {/* Sticky Bottom Action */}
      {!savedSummary ? (
        <View style={styles.stickyBottomWrapper}>
          <PrimaryButton
            title={selectedCount > 0 ? (selectedCount === 1 ? 'Add 1 book' : `Add ${selectedCount} books`) : 'Add selected books'}
            variant="leather"
            onPress={handleAddSelectedToLibrary}
            disabled={selectedCount === 0}
            loading={savingBooks}
            icon={<MaterialIcons name="library-add" size={22} color={colors.leatherGold} />}
            style={styles.stickyAddBtn}
          />
        </View>
      ) : null}

      {/* Correction Modal */}
      {activeItemForCorrection ? (
        <CorrectionModal
          visible={Boolean(activeCorrectionId)}
          itemId={activeCorrectionId!}
          initialTitle={
            activeItemForCorrection.customTitle ||
            activeItemForCorrection.selectedCandidate?.title ||
            activeItemForCorrection.item.extraction.title
          }
          initialAuthor={
            activeItemForCorrection.customAuthor ||
            activeItemForCorrection.selectedCandidate?.author ||
            activeItemForCorrection.item.extraction.author
          }
          onClose={() => setActiveCorrectionId(null)}
          onConfirmCanonical={handleModalConfirmCanonical}
          onConfirmManual={handleModalConfirmManual}
        />
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scroll: {
    flex: 1,
  },
  content: {
    padding: spacing.lg,
    paddingBottom: 180,
    maxWidth: 600,
    width: '100%',
    alignSelf: 'center',
  },
  header: {
    marginTop: spacing.sm,
    marginBottom: spacing.md,
  },
  headerTitle: {
    color: colors.textPrimary,
  },
  successBanner: {
    backgroundColor: colors.surface,
    borderColor: colors.matched.border,
    borderWidth: 1,
    borderRadius: radius.lg,
    padding: spacing.xl,
    alignItems: 'center',
    marginBottom: spacing.xl,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  successIconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.matched.solid,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  successTitle: {
    color: colors.textPrimary,
    textAlign: 'center',
  },
  dupNote: {
    color: colors.textSecondary,
    marginTop: 2,
  },
  successActions: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.lg,
    width: '100%',
  },
  successBtn: {
    flex: 1,
  },
  summaryCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.borderLight,
    marginBottom: spacing.xl,
  },
  summaryText: {
    color: colors.textSecondary,
    lineHeight: 26,
  },
  highlightMatched: {
    color: colors.matched.text,
    fontWeight: '600',
  },
  highlightReview: {
    color: colors.needsReview.text,
    fontWeight: '600',
  },
  highlightUnmatched: {
    color: colors.textPrimary,
    fontWeight: '600',
  },
  highlightUnreadable: {
    color: colors.failed.text,
    fontWeight: '600',
  },
  saveErrorBox: {
    backgroundColor: colors.failed.bg,
    padding: spacing.md,
    borderRadius: radius.md,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.failed.border,
  },
  saveErrorText: {
    color: colors.failed.text,
  },
  groupSection: {
    marginBottom: spacing.xl,
  },
  groupHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
    marginBottom: spacing.md,
  },
  groupHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  groupTitle: {
    color: colors.textPrimary,
    fontSize: 16,
    fontWeight: '700',
  },
  groupTitleReview: {
    color: colors.needsReview.text,
    fontSize: 16,
    fontWeight: '700',
  },
  groupTitleFailed: {
    color: colors.failed.text,
    fontSize: 16,
    fontWeight: '700',
  },
  countBadge: {
    backgroundColor: colors.leather,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: radius.full,
    marginLeft: 4,
  },
  countBadgeText: {
    color: colors.leatherGold,
    fontSize: 11,
    fontWeight: '700',
  },
  countBadgeSecondary: {
    backgroundColor: colors.surfaceContainer,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: radius.full,
    marginLeft: 4,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  countBadgeTextSec: {
    color: colors.textSecondary,
    fontSize: 11,
    fontWeight: '700',
  },
  cardsContainer: {},
  stickyBottomWrapper: {
    position: 'absolute',
    bottom: spacing.lg,
    left: spacing.lg,
    right: spacing.lg,
    maxWidth: 420,
    width: '100%',
    alignSelf: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 8,
  },
  stickyAddBtn: {
    width: '100%',
  },
});
