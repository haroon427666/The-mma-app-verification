/** EventDetailScreen — refactored using detail section components */

import React from 'react';
import { ScrollView, RefreshControl, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '@/hooks/useTheme';
import { spacing } from '@/theme';
import { useEvent, useCountdown, useWatchlist } from '../hooks';
import { useWatchEvent, useUnwatchEvent } from '../mutations/useWatchEvent';
import {
  EventHero, EventInformation, FightCardSection,
  BroadcastSection, VenueSection,
} from '../detail';
import { Countdown } from '../components/Countdown';
import { WatchlistButton } from '../components/WatchlistButton';
import { DetailSkeleton } from '../skeletons';
import { NetworkError, EventNotFound } from '../errors';
import { isLive, isCompleted } from '../utils/eventStatus';
import { eventsAnalytics } from '../analytics/track';

export function EventDetailScreen({ route, navigation }: any) {
  const { eventId } = route.params;
  const { palette } = useTheme();
  const { data: event, isLoading, isError, refetch } = useEvent(eventId);
  const countdown = useCountdown(event?.startTime ?? null);
  const { isWatched } = useWatchlist(eventId);
  const watchEvent = useWatchEvent();
  const unwatchEvent = useUnwatchEvent();

  React.useEffect(() => {
    if (event) eventsAnalytics.eventOpened(eventId, event.name);
  }, [eventId, event]);

  if (isLoading) return <DetailSkeleton />;
  if (isError) return <NetworkError onRetry={refetch} />;
  if (!event) return <EventNotFound onBack={() => navigation.goBack()} />;

  const live = isLive(event);
  const done = isCompleted(event);

  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView refreshControl={<RefreshControl refreshing={false} onRefresh={refetch} tintColor={palette.primary[400]} />}>
        <EventHero event={event} palette={palette} live={live} />
        <EventInformation event={event} palette={palette} />

        {!live && !done && !countdown.isPast && <Countdown state={countdown} palette={palette} />}

        <FightCardSection
          event={event} palette={palette}
          onFightPress={(fightId: string) => {
            eventsAnalytics.fightClicked(fightId, event.fights?.[0]?.fighterA?.fullName ?? '', event.fights?.[0]?.fighterB?.fullName ?? '');
            navigation.navigate('FightCard', { eventId, fightId });
          }}
        />

        <BroadcastSection event={event} palette={palette} />
        <VenueSection event={event} palette={palette} />

        {done && event.results && (
          <View style={[s.btn, { marginHorizontal: spacing.lg, marginBottom: spacing.lg }]}>
            <TouchableOpacity onPress={() => navigation.navigate('Results', { eventId })} style={[s.link, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
              <Text style={[typography.body, { color: palette.primary[400], fontWeight: '600' }]}>View Results →</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>

      {!done && (
        <View style={[s.actions, { backgroundColor: palette.surface.card, borderTopColor: palette.surface.border }]}>
          <WatchlistButton isWatched={isWatched} onToggle={() => isWatched ? unwatchEvent.mutate(eventId) : watchEvent.mutate(eventId)} palette={palette} />
        </View>
      )}
    </SafeAreaView>
  );
}

import { View, Text, TouchableOpacity } from 'react-native';
import { typography, radius } from '@/theme';
const s = StyleSheet.create({
  root: { flex: 1 },
  actions: { flexDirection: 'row', padding: spacing.md, borderTopWidth: 0.5, gap: 8 },
  btn: {},
  link: { padding: spacing.md, borderRadius: radius.md, borderWidth: 0.5 },
});
