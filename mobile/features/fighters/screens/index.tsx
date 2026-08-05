/** Fighters screens — complete profile, stats, history, comparison, similar, achievements, media */

import React, { useCallback } from 'react';
import { View, Text, FlatList, TouchableOpacity, ScrollView, StyleSheet, RefreshControl, Dimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { typography, spacing, radius } from '@/theme';
import { useTheme } from '@/hooks/useTheme';
import { useFighter, useStats, useHistory, useSimilarFighters, useFighters, fightersActions } from '../hooks';
import { useFavoriteFighter, useUnfavoriteFighter } from '../mutations';
import { useIsFavorite } from '../hooks';
import { useFightersStore } from '../store';
import { FighterHeader, FighterRecord, FighterStats as FighterStatsComp, FightHistoryRow, SimilarityCard, FavoriteButton } from '../components';
import { FighterCardSkeleton, ProfileSkeleton, EmptyState, ErrorState } from '../components';
import { RadarChart, LineChart } from '../charts';
import { WEIGHT_CLASSES } from '../constants';

// ── FightersScreen ──
export function FightersScreen({ navigation }: any) {
  const { palette } = useTheme();
  const { selectedWeightClass } = useFightersStore();
  const { data, fetchNextPage, isLoading, refetch } = useFighters();

  const allFighters = data?.pages.flat() ?? [];
  return (
    <SafeAreaView style={[st.root, { backgroundColor: palette.surface.bg }]}>
      <FlatList horizontal data={['All', ...WEIGHT_CLASSES]} showsHorizontalScrollIndicator={false}
        contentContainerStyle={st.chipRow}
        keyExtractor={(d) => d}
        renderItem={({ item }) => (
          <TouchableOpacity onPress={() => fightersActions.setWeightClass(item === 'All' ? null : item)}
            style={[st.chip, { backgroundColor: (selectedWeightClass === item || (!selectedWeightClass && item === 'All')) ? palette.primary[500] : palette.surface.card, borderColor: palette.surface.border }]}>
            <Text style={[typography.bodySmall, { color: (selectedWeightClass === item || (!selectedWeightClass && item === 'All')) ? '#FFF' : palette.text.secondary, fontWeight: '600' }]}>{item}</Text>
          </TouchableOpacity>
        )}
      />
      <FlatList data={allFighters}
        keyExtractor={(f) => f.id}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} />}
        onEndReached={() => fetchNextPage()}
        renderItem={({ item }) => <FighterRow item={item} palette={palette} onPress={() => navigation.navigate('FighterProfile', { fighterId: item.id })} />}
        ListEmptyComponent={!isLoading ? <EmptyState message="No fighters found" palette={palette} /> : <FighterCardSkeleton />}
      />
    </SafeAreaView>
  );
}

function FighterRow({ item, palette, onPress }: any) {
  return (
    <TouchableOpacity onPress={onPress} style={[st.row, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <View style={[st.avatar, { backgroundColor: palette.surface.elevated }]}><Text style={{ fontSize: 22 }}>🥊</Text></View>
      <View style={{ flex: 1, marginLeft: 12 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{item.fullName || item.lastName}</Text>
          {item.isChampion && <Text style={{ marginLeft: 4 }}>👑</Text>}
        </View>
        <Text style={[typography.caption, { color: palette.text.secondary }]}>{item.record || `${item.wins}-${item.losses}`} • {item.weightClass}</Text>
        {item.streak > 0 && <Text style={[typography.caption, { color: '#10B981' }]}>W{item.streak}</Text>}
      </View>
      <View style={{ alignItems: 'flex-end' }}>
        {item.latestRank && <Text style={[typography.title, { color: '#F59E0B' }]}>#{item.latestRank}</Text>}
        {item.eloRating && <Text style={[typography.mono, { color: palette.text.tertiary }]}>{Math.round(item.eloRating)}</Text>}
      </View>
    </TouchableOpacity>
  );
}

// ── FighterProfileScreen ──
export function FighterProfileScreen({ route, navigation }: any) {
  const { fighterId } = route.params;
  const { palette } = useTheme();
  const { data: fighter, isLoading } = useFighter(fighterId);
  const { data: stats } = useStats(fighterId);
  const { data: similar } = useSimilarFighters(fighterId);
  const { data: isFav } = useIsFavorite(fighterId);
  const fav = useFavoriteFighter();
  const unfav = useUnfavoriteFighter();
  const { tab } = useFightersStore();

  if (isLoading) return <ProfileSkeleton />;
  if (!fighter) return <ErrorState message="Fighter not found" palette={palette} />;

  return (
    <SafeAreaView style={[st.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView refreshControl={<RefreshControl refreshing={false} onRefresh={() => {}} />}>
        <FighterHeader fighter={fighter} palette={palette} />
        <FighterRecord fighter={fighter} palette={palette} />

        <View style={st.actions}>
          <FavoriteButton isFav={!!isFav} onToggle={() => isFav ? unfav.mutate(fighterId) : fav.mutate(fighterId)} palette={palette} />
          <TouchableOpacity style={[st.actionBtn, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}
            onPress={() => navigation.navigate('FighterComparison', { fighterA: fighterId })}>
            <Text style={[typography.bodySmall, { color: palette.text.primary }]}>⚖️ Compare</Text>
          </TouchableOpacity>
        </View>

        {/* Tabs */}
        <View style={st.tabs}>
          {(['overview', 'stats', 'history', 'similar'] as const).map((t) => (
            <TouchableOpacity key={t} onPress={() => fightersActions.setTab(t as any)} style={[st.tab, tab === t && { borderBottomColor: palette.primary[400], borderBottomWidth: 2 }]}>
              <Text style={[typography.bodySmall, { color: tab === t ? palette.primary[400] : palette.text.tertiary, fontWeight: '600', textTransform: 'capitalize' }]}>{t}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {tab === 'overview' && (
          <View style={st.section}>
            {stats && <RadarChart stats={stats} palette={palette} />}
            {similar && similar.length > 0 && (
              <View>
                <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: spacing.sm }]}>Similar Fighters</Text>
                {similar.slice(0, 4).map((s: any, i: number) => <SimilarityCard key={i} item={s} palette={palette} />)}
              </View>
            )}
          </View>
        )}

        {tab === 'stats' && stats && <FighterStatsComp stats={stats} fighter={fighter} palette={palette} />}
        {tab === 'history' && <FightHistoryTab fighterId={fighterId} palette={palette} navigation={navigation} />}
        {tab === 'similar' && <SimilarTab fighterId={fighterId} palette={palette} />}
      </ScrollView>
    </SafeAreaView>
  );
}

function FightHistoryTab({ fighterId, palette }: any) {
  const { data, fetchNextPage } = useHistory(fighterId);
  const fights = data?.pages.flat() ?? [];
  return (
    <View style={st.section}>
      {fights.map((f: any, i: number) => <FightHistoryRow key={i} fight={f} palette={palette} />)}
      {fights.length === 0 && <EmptyState message="No fight history" palette={palette} />}
    </View>
  );
}

function SimilarTab({ fighterId, palette }: any) {
  const { data: similar } = useSimilarFighters(fighterId);
  return (
    <View style={st.section}>
      {(similar ?? []).map((s: any, i: number) => <SimilarityCard key={i} item={s} palette={palette} />)}
    </View>
  );
}

// ── FighterComparisonScreen ──
export function FighterComparisonScreen({ route }: any) {
  const { fighterA, fighterB } = route.params;
  const { palette } = useTheme();
  const { data: fa } = useFighter(fighterA);
  const { data: fb } = useFighter(fighterB);
  if (!fa) return <FighterCardSkeleton />;

  return (
    <SafeAreaView style={[st.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView contentContainerStyle={st.section}>
        <Text style={[typography.headline, { color: palette.text.primary, textAlign: 'center' }]}>{fa.fullName} vs {fb?.fullName ?? '?'}</Text>
        <View style={st.compareGrid}>
          <CompCol fighter={fa} palette={palette} label="A" />
          <View style={{ justifyContent: 'center' }}><Text style={[typography.title, { color: palette.text.tertiary }]}>VS</Text></View>
          <CompCol fighter={fb} palette={palette} label="B" />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function CompCol({ fighter, palette, label }: any) {
  if (!fighter) return <View style={{ flex: 1, alignItems: 'center', padding: spacing.lg }}><Text style={{ color: palette.text.tertiary }}>Select fighter</Text></View>;
  return (
    <View style={{ flex: 1, alignItems: 'center', padding: spacing.md }}>
      <View style={[st.avatar, { backgroundColor: palette.surface.elevated }]}><Text>🥊</Text></View>
      <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600', marginTop: 8 }]}>{fighter.lastName}</Text>
      <Text style={[typography.caption, { color: palette.text.secondary }]}>{fighter.record || `${fighter.wins}-${fighter.losses}`}</Text>
      {fighter.latestRank && <Text style={[typography.caption, { color: '#F59E0B' }]}>#{fighter.latestRank}</Text>}
    </View>
  );
}

// ── Placeholder screens ──
export function FighterStatsScreen({ route }: any) { const { palette } = useTheme(); return <SafeAreaView style={[st.root, { backgroundColor: palette.surface.bg }]}><FighterProfileScreen route={route} /></SafeAreaView>; }
export function SimilarFightersScreen({ route }: any) { return <FighterComparisonScreen route={route} />; }
export function AchievementsScreen({ route }: any) { const { palette } = useTheme(); return <SafeAreaView style={[st.root, { backgroundColor: palette.surface.bg }]}><Text style={[typography.body, { color: palette.text.secondary, padding: spacing.xl }]}>Achievements coming soon</Text></SafeAreaView>; }
export function MediaScreen({ route }: any) { const { palette } = useTheme(); return <SafeAreaView style={[st.root, { backgroundColor: palette.surface.bg }]}><Text style={[typography.body, { color: palette.text.secondary, padding: spacing.xl }]}>Media coming soon</Text></SafeAreaView>; }

const st = StyleSheet.create({
  root: { flex: 1 },
  chipRow: { paddingHorizontal: spacing.lg, paddingVertical: spacing.md, gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, borderWidth: 1 },
  row: { flexDirection: 'row', alignItems: 'center', padding: spacing.md, marginHorizontal: spacing.lg, marginBottom: 8, borderRadius: radius.md, borderWidth: 0.5 },
  avatar: { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center' },
  actions: { flexDirection: 'row', paddingHorizontal: spacing.lg, gap: 8, marginVertical: spacing.md },
  actionBtn: { flex: 1, paddingVertical: 12, borderRadius: radius.md, borderWidth: 1, alignItems: 'center' },
  tabs: { flexDirection: 'row', borderBottomWidth: 0.5, borderBottomColor: '#2A2A3E', marginTop: spacing.md },
  tab: { flex: 1, paddingVertical: 14, alignItems: 'center' },
  section: { padding: spacing.lg },
  compareGrid: { flexDirection: 'row', justifyContent: 'space-around', marginTop: spacing.xl },
});
