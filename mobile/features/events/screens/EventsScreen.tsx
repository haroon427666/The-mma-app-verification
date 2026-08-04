/** Events screen — featured, live, upcoming, past with filters and infinite scroll */

import React from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '@/hooks/useTheme';
import { typography, spacing, radius } from '@/theme';
import { useEvents, useLiveEvents } from '../hooks';
import { useEventsStore, eventsActions } from '../store/events.store';
import { EventCard } from '../components/EventCard';
import { LiveBanner } from '../components/LiveBanner';
import { EventCardSkeleton } from '../skeletons';
import { ErrorCard } from '../components/SupportComponents';
import type { EventFilter, ExtendedEvent } from '../types';

const FILTERS: { key: EventFilter; label: string }[] = [
  { key: 'live', label: 'Live' },
  { key: 'upcoming', label: 'Upcoming' },
  { key: 'thisWeek', label: 'This Week' },
  { key: 'thisMonth', label: 'This Month' },
  { key: 'past', label: 'Past' },
];

export function EventsScreen({ navigation }: any) {
  const { palette } = useTheme();
  const { activeFilter } = useEventsStore();
  const { data: liveEvents } = useLiveEvents();
  const { data, fetchNextPage, hasNextPage, isFetching, isLoading, isError, refetch } = useEvents();

  const allEvents = data?.pages.flat() ?? [];

  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      {/* Filter chips */}
      <FlatList
        horizontal
        data={FILTERS}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={s.chipRow}
        keyExtractor={(f) => f.key}
        renderItem={({ item }) => (
          <TouchableOpacity
            onPress={() => eventsActions.setFilter(item.key)}
            style={[s.chip, { backgroundColor: activeFilter === item.key ? palette.primary[500] : palette.surface.card, borderColor: palette.surface.border }]}
          >
            <Text style={[typography.bodySmall, { color: activeFilter === item.key ? '#FFF' : palette.text.secondary, fontWeight: '600' }]}>
              {item.label}
            </Text>
          </TouchableOpacity>
        )}
      />

      {/* Live banner */}
      {liveEvents && liveEvents.length > 0 && activeFilter !== 'past' && (
        <LiveBanner
          event={liveEvents[0] as ExtendedEvent}
          palette={palette}
          onPress={() => navigation.navigate('EventDetail', { eventId: liveEvents[0].id })}
        />
      )}

      {/* Event list */}
      <FlatList
        data={allEvents}
        keyExtractor={(e) => e.id}
        refreshControl={<RefreshControl refreshing={isFetching && !isLoading} onRefresh={refetch} tintColor={palette.primary[400]} />}
        onEndReached={() => hasNextPage && fetchNextPage()}
        onEndReachedThreshold={0.5}
        renderItem={({ item }) => (
          <EventCard event={item} palette={palette} onPress={() => navigation.navigate('EventDetail', { eventId: item.id })} />
        )}
        ListEmptyComponent={!isLoading && !isError ? (
          <Text style={[typography.body, { color: palette.text.secondary, textAlign: 'center', marginTop: 60 }]}>No events found</Text>
        ) : null}
        ListHeaderComponent={isLoading ? <EventCardSkeleton /> : null}
      />
      {isError && <ErrorCard onRetry={refetch} />}
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  chipRow: { paddingHorizontal: spacing.lg, paddingVertical: spacing.md, gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, borderWidth: 1 },
});
