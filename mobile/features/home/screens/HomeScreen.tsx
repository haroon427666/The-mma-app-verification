/** Home screen — live events, upcoming, recommendations */

import React, { useCallback } from 'react';
import { View, Text, ScrollView, RefreshControl, StyleSheet, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { useTheme } from '@/hooks/useTheme';
import api from '@/services/api';
import { typography, spacing, radius } from '@/theme';
import type { HomeFeed, Event } from '@/features/models';
export function HomeScreen({ navigation }: any) {
  const { palette } = useTheme();
  const { data, isLoading, isError, refetch } = useQuery<HomeFeed>({
    queryKey: ['home'],
    queryFn: async () => {
      const [{ data: live }, { data: upcoming }, { data: recs }, { data: titles }] = await Promise.all([
        api.get('/v1/events/live?limit=3'),
        api.get('/v1/events/upcoming?limit=5'),
        api.get('/v1/recommendations/fighters?limit=6'),
        api.get('/v1/fights?is_title=true&status=SCHEDULED&limit=5'),
      ]);
      return {
        liveEvents: live?.data ?? [],
        upcomingEvents: upcoming?.data ?? [],
        trendingFighters: [],
        recommendedFighters: recs?.data ?? [],
        upcomingTitleFights: titles?.data ?? [],
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
  skelBlock: { height: 80, borderRadius: radius.md, marginBottom: 12 },
  retryBtn: { marginTop: 24, paddingVertical: 14, paddingHorizontal: 32, borderRadius: radius.md },
});
