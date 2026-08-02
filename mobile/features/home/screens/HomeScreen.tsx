/** Home screen — live events, recommended, trending, predictions */

import React, { useCallback } from 'react';
import { View, Text, ScrollView, RefreshControl, StyleSheet, TouchableOpacity, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { useTheme } from '@/hooks/useTheme';
import api from '@/services/api';
import { typography, spacing, radius } from '@/theme';
import type { HomeFeed, Fighter, Event } from '@/features/models';

export function HomeScreen({ navigation }: any) {
  const { palette } = useTheme();
  const { data, isLoading, isError, refetch } = useQuery<HomeFeed>({
    queryKey: ['home'],
    queryFn: async () => {
      const [{ data: live }, { data: upcoming }, { data: trending }] = await Promise.all([
        api.get('/v1/events?status=LIVE,IN_PROGRESS&limit=3'),
        api.get('/v1/events/upcoming?limit=5'),
        api.get('/v1/fighters/trending?limit=6'),
      ]);
      return {
        liveEvents: live?.data ?? [],
        upcomingEvents: upcoming?.data ?? [],
        trendingFighters: trending?.data ?? [],
        recommendedFighters: [],
        upcomingTitleFights: [],
        predictionHighlights: [],
        recentRankingChanges: [],
      };
    },
    staleTime: 2 * 60 * 1000,
  });

  if (isLoading) return <HomeSkeleton palette={palette} />;
  if (isError) return <HomeError onRetry={() => refetch()} palette={palette} />;

  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView refreshControl={<RefreshControl refreshing={false} onRefresh={refetch} tintColor={palette.primary[400]} />}>
        <Text style={[typography.headline, { color: palette.text.primary, padding: spacing.lg }]}>MMA Intelligence</Text>

        {data?.liveEvents && data.liveEvents.length > 0 && (
          <Section title="🔴 Live Now" palette={palette}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.hScroll}>
              {data.liveEvents.map((event) => <EventCard key={event.id} event={event} palette={palette} onPress={() => navigation.navigate('events', { screen: 'eventDetail', params: { id: event.id } })} />)}
            </ScrollView>
          </Section>
        )}

        {data?.upcomingEvents && data.upcomingEvents.length > 0 && (
          <Section title="Upcoming Events" palette={palette}>
            {data.upcomingEvents.slice(0,3).map((event) => <EventRow key={event.id} event={event} palette={palette} />)}
          </Section>
        )}

        {data?.trendingFighters && data.trendingFighters.length > 0 && (
          <Section title="📈 Trending Fighters" palette={palette}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.hScroll}>
              {data.trendingFighters.map((f) => <FighterCard key={f.id} fighter={f} palette={palette} />)}
            </ScrollView>
          </Section>
        )}
        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

function Section({ title, palette, children }: any) {
  return (
    <View style={s.section}>
      <Text style={[typography.title, { color: palette.text.primary, marginBottom: spacing.md }]}>{title}</Text>
      {children}
    </View>
  );
}

function EventCard({ event, palette, onPress }: { event: Event; palette: any; onPress: () => void }) {
  return (
    <TouchableOpacity onPress={onPress} style={[s.cardLarge, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <View style={[s.liveDot, { backgroundColor: '#EF4444' }]} />
      <Text style={[typography.bodySmall, { color: '#EF4444', fontWeight: '700' }]}>LIVE</Text>
      <Text style={[typography.subtitle, { color: palette.text.primary, marginTop: 4 }]} numberOfLines={2}>{event.name}</Text>
      <Text style={[typography.caption, { color: palette.text.secondary, marginTop: 4 }]}>{event.venue} • {event.fightCount} fights</Text>
    </TouchableOpacity>
  );
}

function EventRow({ event, palette }: { event: Event; palette: any }) {
  return (
    <TouchableOpacity style={[s.row, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <View style={{ flex: 1 }}>
        <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{event.name}</Text>
        <Text style={[typography.caption, { color: palette.text.secondary }]}>{new Date(event.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} • {event.venue}</Text>
      </View>
      <Text style={[typography.mono, { color: palette.primary[400] }]}>{event.fightCount} fights</Text>
    </TouchableOpacity>
  );
}

function FighterCard({ fighter, palette }: { fighter: Fighter; palette: any }) {
  return (
    <TouchableOpacity style={[s.fighterCard, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <View style={[s.avatar, { backgroundColor: palette.surface.elevated }]}>
        <Text style={{ fontSize: 24 }}>🥊</Text>
      </View>
      <Text style={[typography.bodySmall, { color: palette.text.primary, fontWeight: '600', marginTop: 8 }]} numberOfLines={2}>{fighter.fullName || fighter.lastName}</Text>
      <Text style={[typography.caption, { color: palette.text.secondary }]}>{fighter.record}</Text>
      {fighter.latestRank && <Text style={[typography.caption, { color: '#F59E0B' }]}>#{fighter.latestRank} {fighter.weightClass}</Text>}
    </TouchableOpacity>
  );
}

function HomeSkeleton({ palette }: any) {
  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <View style={{ padding: spacing.lg }}>
        {[1,2,3,4].map((i) => (
          <View key={i} style={[s.skelBlock, { backgroundColor: palette.surface.card }]} />
        ))}
      </View>
    </SafeAreaView>
  );
}

function HomeError({ onRetry, palette }: any) {
  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg, justifyContent: 'center', alignItems: 'center' }]}>
      <Text style={{ fontSize: 48 }}>📡</Text>
      <Text style={[typography.title, { color: palette.text.primary, marginTop: 16 }]}>Couldn't load feed</Text>
      <TouchableOpacity onPress={onRetry} style={[s.retryBtn, { backgroundColor: palette.primary[500] }]}>
        <Text style={{ color: '#FFF', fontWeight: '600' }}>Retry</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  section: { paddingHorizontal: spacing.lg, marginBottom: spacing.xl },
  hScroll: { paddingRight: spacing.lg, gap: 12 },
  cardLarge: { width: 220, padding: spacing.lg, borderRadius: radius.lg, borderWidth: 0.5, marginRight: 12 },
  liveDot: { width: 8, height: 8, borderRadius: 4, marginBottom: 8 },
  row: { flexDirection: 'row', alignItems: 'center', padding: spacing.md, borderRadius: radius.md, borderWidth: 0.5, marginBottom: 8 },
  fighterCard: { width: 120, padding: spacing.md, borderRadius: radius.lg, borderWidth: 0.5, marginRight: 12, alignItems: 'center' },
  avatar: { width: 56, height: 56, borderRadius: 28, alignItems: 'center', justifyContent: 'center', marginBottom: 4 },
  skelBlock: { height: 80, borderRadius: radius.md, marginBottom: 12 },
  retryBtn: { marginTop: 24, paddingVertical: 14, paddingHorizontal: 32, borderRadius: radius.md },
});
