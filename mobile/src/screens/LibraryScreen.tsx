import React, { useState, useEffect, useMemo } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TextInput,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { colors } from '../theme/colors';
import { spacing, radius } from '../theme/spacing';
import { typography } from '../theme/typography';
import { EmptyState } from '../components/EmptyState';
import { PrimaryButton } from '../components/PrimaryButton';
import { apiClient } from '../api/client';
import { LibraryBook } from '../api/types';

interface LibraryScreenProps {
  onNavigateScan: () => void;
}

export const LibraryScreen: React.FC<LibraryScreenProps> = ({ onNavigateScan }) => {
  const [books, setBooks] = useState<LibraryBook[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchLibrary = async (isPullToRefresh = false) => {
    if (!isPullToRefresh) setLoading(true);
    setErrorMessage(null);
    try {
      const data = await apiClient.getLibrary();
      setBooks(data.books || []);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load personal library.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchLibrary();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchLibrary(true);
  };

  // Client-side search filtering
  const filteredBooks = useMemo(() => {
    if (!searchQuery.trim()) return books;
    const q = searchQuery.toLowerCase().trim();
    return books.filter(
      (b) =>
        b.confirmed_title.toLowerCase().includes(q) ||
        (b.confirmed_author && b.confirmed_author.toLowerCase().includes(q)) ||
        (b.edition && b.edition.toLowerCase().includes(q))
    );
  }, [books, searchQuery]);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          tintColor={colors.leather}
        />
      }
      keyboardShouldPersistTaps="handled"
    >
      {/* Screen Header */}
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text style={[typography.headlineLarge, styles.title]}>My Library</Text>
          <Text style={[typography.bodySmall, styles.subtitle]}>
            {books.length} {books.length === 1 ? 'book' : 'books'} in collection
          </Text>
        </View>
        <PrimaryButton
          title="+ Scan Shelf"
          variant="leather"
          onPress={onNavigateScan}
          icon={<MaterialCommunityIcons name="barcode-scan" size={16} color={colors.leatherGold} />}
          style={styles.scanBtn}
          textStyle={styles.scanBtnText}
        />
      </View>

      {/* Error Notice */}
      {errorMessage ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{errorMessage}</Text>
          <PrimaryButton
            title="Retry"
            variant="ghost"
            onPress={() => fetchLibrary()}
            style={styles.retryBtn}
          />
        </View>
      ) : null}

      {/* Loading Indicator */}
      {loading ? (
        <View style={styles.loadingBox}>
          <ActivityIndicator size="large" color={colors.leather} />
          <Text style={[typography.bodySmall, styles.loadingText]}>Loading your collection...</Text>
        </View>
      ) : books.length === 0 ? (
        /* Empty Library State */
        <EmptyState
          iconName="book-open-page-variant"
          title="Your library is empty."
          description="Scan a shelf to add your first books."
          actionTitle="Scan a shelf"
          onAction={onNavigateScan}
        />
      ) : (
        /* Populated Library List */
        <View style={styles.listContainer}>
          {/* Search Input matching Stitch design */}
          <View style={styles.searchRow}>
            <Feather name="search" size={18} color={colors.textSecondary} style={styles.searchIcon} />
            <TextInput
              style={styles.searchInput}
              placeholder="Search books"
              placeholderTextColor={colors.textMuted}
              value={searchQuery}
              onChangeText={setSearchQuery}
              clearButtonMode="while-editing"
            />
          </View>

          {filteredBooks.length === 0 ? (
            <View style={styles.noSearchMatchBox}>
              <Text style={[typography.bodyMedium, styles.noMatchText]}>
                No books matching "{searchQuery}".
              </Text>
            </View>
          ) : (
            filteredBooks.map((book) => {
              const dateStr = book.added_at
                ? new Date(book.added_at).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })
                : null;

              return (
                <View key={book.id} style={styles.bookRow}>
                  <View style={styles.bookMain}>
                    <Text style={[typography.headlineSmall, styles.bookTitle]} numberOfLines={2}>
                      {book.confirmed_title}
                    </Text>
                    <Text style={[typography.bodyMedium, styles.bookAuthor]}>
                      {book.confirmed_author ? book.confirmed_author : 'Unknown Author'}
                    </Text>

                    {/* Metadata Badges */}
                    <View style={styles.badgesRow}>
                      {book.edition ? (
                        <View style={styles.metaPill}>
                          <Text style={[typography.labelSmall, styles.metaPillText]}>
                            {book.edition}
                          </Text>
                        </View>
                      ) : null}

                      {book.catalog_id ? (
                        <View style={styles.catalogPill}>
                          <Text style={[typography.labelSmall, styles.catalogPillText]}>
                            {book.catalog_id}
                          </Text>
                        </View>
                      ) : (
                        <View style={styles.customPill}>
                          <Text style={[typography.labelSmall, styles.customPillText]}>
                            Custom
                          </Text>
                        </View>
                      )}

                      {dateStr ? (
                        <Text style={[typography.labelSmall, styles.dateText]}>{dateStr}</Text>
                      ) : null}
                    </View>
                  </View>
                </View>
              );
            })
          )}
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.xl,
    paddingTop: spacing.sm,
  },
  headerText: {
    flex: 1,
    marginRight: spacing.md,
  },
  title: {
    color: colors.textPrimary,
  },
  subtitle: {
    color: colors.textSecondary,
    marginTop: 2,
  },
  scanBtn: {
    minHeight: 40,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  scanBtnText: {
    fontSize: 14,
  },
  errorBox: {
    backgroundColor: colors.failed.bg,
    padding: spacing.md,
    borderRadius: radius.md,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.failed.border,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  errorText: {
    color: colors.failed.text,
    flex: 1,
  },
  retryBtn: {
    minHeight: 32,
    paddingVertical: 0,
  },
  loadingBox: {
    padding: spacing.huge,
    alignItems: 'center',
  },
  loadingText: {
    marginTop: spacing.md,
    color: colors.textSecondary,
  },
  listContainer: {
    width: '100%',
  },
  searchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingBottom: spacing.sm,
    marginBottom: spacing.xxl,
  },
  searchIcon: {
    marginRight: spacing.sm,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: colors.textPrimary,
    paddingVertical: spacing.xs,
  },
  noSearchMatchBox: {
    padding: spacing.xl,
    alignItems: 'center',
  },
  noMatchText: {
    color: colors.textMuted,
  },
  bookRow: {
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
    paddingBottom: spacing.lg,
    marginBottom: spacing.lg,
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  bookMain: {
    flex: 1,
  },
  bookTitle: {
    color: colors.textPrimary,
    marginBottom: 2,
  },
  bookAuthor: {
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  badgesRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  metaPill: {
    backgroundColor: colors.borderLight,
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: 3,
    borderRadius: radius.md,
  },
  metaPillText: {
    color: colors.textSecondary,
    fontSize: 11,
  },
  catalogPill: {
    backgroundColor: colors.surfaceContainer,
    borderWidth: 1,
    borderColor: colors.borderLight,
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: 2,
    borderRadius: radius.md,
  },
  catalogPillText: {
    color: colors.leather,
    fontSize: 11,
    fontWeight: '700',
  },
  customPill: {
    backgroundColor: colors.surfaceContainer,
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: 2,
    borderRadius: radius.md,
  },
  customPillText: {
    color: colors.textSecondary,
    fontSize: 11,
  },
  dateText: {
    color: colors.textMuted,
    marginLeft: 2,
  },
});
