import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  Modal,
  TextInput,
  TouchableOpacity,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import { spacing, radius } from '../theme/spacing';
import { typography } from '../theme/typography';
import { PrimaryButton } from './PrimaryButton';
import { StatusBadge } from './StatusBadge';
import { apiClient } from '../api/client';
import { CatalogCandidate, MatchCorrectionResponse } from '../api/types';

interface CorrectionModalProps {
  visible: boolean;
  initialTitle?: string | null;
  initialAuthor?: string | null;
  itemId: string;
  onClose: () => void;
  onConfirmCanonical: (candidate: CatalogCandidate, confidence: number) => void;
  onConfirmManual: (title: string, author: string) => void;
}

export const CorrectionModal: React.FC<CorrectionModalProps> = ({
  visible,
  initialTitle,
  initialAuthor,
  itemId,
  onClose,
  onConfirmCanonical,
  onConfirmManual,
}) => {
  const [title, setTitle] = useState<string>(initialTitle || '');
  const [author, setAuthor] = useState<string>(initialAuthor || '');
  const [loading, setLoading] = useState<boolean>(false);
  const [matchResult, setMatchResult] = useState<MatchCorrectionResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSearchMatch = async () => {
    if (!title.trim() && !author.trim()) {
      setErrorMsg('Please enter a title or author to search.');
      return;
    }
    setErrorMsg(null);
    setLoading(true);
    try {
      const res = await apiClient.matchBook(title.trim(), author.trim());
      setMatchResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to search canonical catalog.');
    } finally {
      setLoading(false);
    }
  };

  const handleManualAdd = () => {
    if (!title.trim()) {
      setErrorMsg('A title is required for manual library addition.');
      return;
    }
    onConfirmManual(title.trim(), author.trim());
    onClose();
  };

  return (
    <Modal
      visible={visible}
      animationType="fade"
      transparent={true}
      onRequestClose={onClose}
    >
      <KeyboardAvoidingView
        style={styles.overlay}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={styles.modalCard}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={[typography.headlineSmall, styles.modalTitle]}>Correct book</Text>
            <TouchableOpacity
              style={styles.closeBtn}
              onPress={onClose}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            >
              <Feather name="x" size={20} color={colors.textSecondary} />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.scrollArea} keyboardShouldPersistTaps="handled">
            <Text style={[typography.bodySmall, styles.guideText]}>
              We couldn't confidently identify this scan. Please correct the details below.
            </Text>

            {/* Title Field */}
            <View style={styles.fieldBlock}>
              <Text style={[typography.labelMedium, styles.fieldLabel]}>TITLE</Text>
              <View style={styles.inputRow}>
                <TextInput
                  style={styles.input}
                  placeholder="Enter book title"
                  placeholderTextColor={colors.textMuted}
                  value={title}
                  onChangeText={(t) => {
                    setTitle(t);
                    setErrorMsg(null);
                  }}
                  autoCapitalize="words"
                />
                <Feather name="edit-2" size={16} color={colors.textMuted} style={styles.inputIcon} />
              </View>
            </View>

            {/* Author Field */}
            <View style={styles.fieldBlock}>
              <Text style={[typography.labelMedium, styles.fieldLabel]}>AUTHOR</Text>
              <View style={styles.inputRow}>
                <TextInput
                  style={styles.input}
                  placeholder="Enter author name"
                  placeholderTextColor={colors.textMuted}
                  value={author}
                  onChangeText={(a) => {
                    setAuthor(a);
                    setErrorMsg(null);
                  }}
                  autoCapitalize="words"
                />
                <Feather name="user" size={16} color={colors.textMuted} style={styles.inputIcon} />
              </View>
            </View>

            {errorMsg ? <Text style={styles.errorText}>{errorMsg}</Text> : null}

            <PrimaryButton
              title="Find Catalog Match"
              variant="leather"
              onPress={handleSearchMatch}
              loading={loading}
              icon={<MaterialCommunityIcons name="book-search-outline" size={20} color={colors.leatherGold} />}
              style={styles.searchBtn}
            />

            {/* Match Results */}
            {matchResult ? (
              <View style={styles.resultsContainer}>
                <View style={styles.resultHeader}>
                  <Text style={[typography.labelMedium, styles.resultHeaderLabel]}>MATCH RESULT</Text>
                  <StatusBadge
                    state={matchResult.state}
                    confidence={matchResult.confidence}
                  />
                </View>

                {matchResult.best_candidate ? (
                  <View style={styles.candidateCard}>
                    <Text style={[typography.headlineSmall, styles.candTitle]}>
                      {matchResult.best_candidate.title}
                    </Text>
                    <Text style={[typography.bodyMedium, styles.candAuthor]}>
                      {matchResult.best_candidate.author}
                    </Text>
                    {matchResult.best_candidate.edition ? (
                      <Text style={[typography.bodySmall, styles.candEdition]}>
                        Edition: {matchResult.best_candidate.edition}
                      </Text>
                    ) : null}

                    <PrimaryButton
                      title="Use Canonical Match"
                      variant="leather"
                      onPress={() => {
                        onConfirmCanonical(
                          matchResult.best_candidate!,
                          matchResult.confidence
                        );
                        onClose();
                      }}
                      style={styles.selectBtn}
                    />
                  </View>
                ) : null}

                {/* Alternative Candidates */}
                {matchResult.alternatives && matchResult.alternatives.length > 0 ? (
                  <View style={styles.alternativesSection}>
                    <Text style={[typography.labelMedium, styles.altLabel]}>OTHER CATALOG CANDIDATES</Text>
                    {matchResult.alternatives.map((alt) => (
                      <TouchableOpacity
                        key={alt.catalog_id}
                        style={styles.altCard}
                        onPress={() => {
                          onConfirmCanonical(alt, alt.score);
                          onClose();
                        }}
                      >
                        <View style={styles.altInfo}>
                          <Text style={[typography.bodyMedium, styles.altTitle]}>{alt.title}</Text>
                          <Text style={[typography.bodySmall, styles.altAuthor]}>{alt.author}</Text>
                        </View>
                        <Text style={styles.chooseText}>Choose →</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                ) : null}

                {/* Freeform Add Note if Unmatched */}
                {matchResult.state === 'unmatched' ? (
                  <View style={styles.unmatchedSection}>
                    <Text style={[typography.bodySmall, styles.unmatchedNote]}>
                      Not found in the canonical catalog. You can still add this book directly to your personal library.
                    </Text>
                  </View>
                ) : null}
              </View>
            ) : null}
          </ScrollView>

          {/* Footer Actions */}
          <View style={styles.footer}>
            <PrimaryButton
              title="Add As Typed Manually"
              variant="secondary"
              onPress={handleManualAdd}
              style={styles.manualBtn}
            />
            <PrimaryButton
              title="Cancel"
              variant="ghost"
              onPress={onClose}
            />
          </View>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(60, 42, 33, 0.65)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },
  modalCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.borderLight,
    maxWidth: 480,
    width: '100%',
    maxHeight: '88%',
    padding: spacing.xl,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 10,
    elevation: 8,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
    paddingBottom: spacing.sm,
  },
  modalTitle: {
    color: colors.textPrimary,
  },
  closeBtn: {
    padding: 4,
  },
  scrollArea: {
    marginBottom: spacing.sm,
  },
  guideText: {
    color: colors.textSecondary,
    marginBottom: spacing.lg,
  },
  fieldBlock: {
    marginBottom: spacing.lg,
  },
  fieldLabel: {
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingBottom: 4,
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: colors.textPrimary,
    paddingVertical: spacing.xs,
  },
  inputIcon: {
    marginLeft: spacing.sm,
  },
  errorText: {
    color: colors.failed.text,
    fontSize: 13,
    marginBottom: spacing.sm,
  },
  searchBtn: {
    marginVertical: spacing.md,
    width: '100%',
  },
  resultsContainer: {
    backgroundColor: colors.surfaceContainer,
    borderRadius: radius.md,
    padding: spacing.md,
    marginTop: spacing.sm,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  resultHeaderLabel: {
    color: colors.textSecondary,
  },
  candidateCard: {
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.borderLight,
    marginBottom: spacing.md,
  },
  candTitle: {
    color: colors.textPrimary,
  },
  candAuthor: {
    color: colors.textSecondary,
    marginTop: 2,
  },
  candEdition: {
    color: colors.textMuted,
    marginTop: 4,
  },
  selectBtn: {
    marginTop: spacing.md,
  },
  alternativesSection: {
    marginTop: spacing.xs,
  },
  altLabel: {
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  altCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.borderLight,
    marginBottom: spacing.xs,
  },
  altInfo: {
    flex: 1,
    marginRight: spacing.sm,
  },
  altTitle: {
    color: colors.textPrimary,
    fontWeight: '600',
  },
  altAuthor: {
    color: colors.textSecondary,
  },
  chooseText: {
    color: colors.leather,
    fontWeight: '700',
    fontSize: 13,
  },
  unmatchedSection: {
    marginTop: spacing.sm,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.borderLight,
  },
  unmatchedNote: {
    color: colors.textSecondary,
  },
  footer: {
    gap: spacing.xs,
    borderTopWidth: 1,
    borderTopColor: colors.borderLight,
    paddingTop: spacing.md,
  },
  manualBtn: {
    width: '100%',
  },
});
