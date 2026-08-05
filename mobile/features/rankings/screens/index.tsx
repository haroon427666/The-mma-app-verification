/** Rankings Screens — P4P, Division, GOAT, Prospects, Movement, History, Champions */

import React, { useState, useMemo } from 'react';
import { View, Text, FlatList, TouchableOpacity, ScrollView, StyleSheet, RefreshControl, Dimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '@/hooks/useTheme';
import { typography, spacing, radius } from '@/theme';
import { useP4P, useDivisionRankings, useGOAT, useProspects, useRankingMovement, useChampions, useStreaks, useRankingHistory, useTitleDefenses } from '../hooks';
import { useRankingsStore, rankingsActions } from '../stores';
import { rankingAnalytics } from '../services';
import { WEIGHT_CLASSES, rankingColors } from '../theme';
import type { P4PRanking, GOATEntry, ProspectEntry, RankingFighter, RankingHistoryPoint } from '../types';
import { RankingCard } from '../components';

// ── RankingsScreen (Main landing) ──
export function RankingsScreen({ navigation }: any) {
  const { palette } = useTheme();
  const { view } = useRankingsStore();

  const views = [
    { key: 'p4p' as const, label: 'P4P', icon: '👑' },
    { key: 'division' as const, label: 'Divisions', icon: '📊' },
    { key: 'goat' as const, label: 'GOAT', icon: '🐐' },
    { key: 'prospects' as const, label: 'Prospects', icon: '🌟' },
    { key: 'movement' as const, label: 'Movement', icon: '📈' },
  ];

  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <View style={[s.header, { borderBottomColor: palette.surface.border }]}>
        {views.map((v) => (
          <TouchableOpacity key={v.key} onPress={() => rankingsActions.setView(v.key)} style={[s.viewTab, view === v.key && { borderBottomColor: palette.primary[400], borderBottomWidth: 2 }]}>
            <Text style={[typography.bodySmall, { color: view === v.key ? palette.primary[400] : palette.text.tertiary, fontWeight: '600' }]}>{v.icon} {v.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
      {view === 'p4p' && <P4PView palette={palette} navigation={navigation} />}
      {view === 'division' && <DivisionView palette={palette} />}
      {view === 'goat' && <GOATView palette={palette} />}
      {view === 'prospects' && <ProspectsView palette={palette} />}
      {view === 'movement' && <MovementView palette={palette} />}
    </SafeAreaView>
  );
}

// ── P4P View ──
function P4PView({ palette, navigation }: any) {
  const { data, isLoading, refetch } = useP4P();
  return (
    <FlatList
      data={data ?? []}
      keyExtractor={(r) => r.fighter?.id || String(r.rank)}
      refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor={palette.primary[400]} />}
      renderItem={({ item }) => (
        <RankingCard
          rank={item.rank}
          previousRank={item.previousRank}
          movement={item.movement}
          fighter={item.fighter}
          subtitle={`${item.division} • ${item.fighter?.eloRating ? `Elo ${Math.round(item.fighter.eloRating)}` : ''}`}
          extra={<Text style={[styles.mono, { color: palette.primary[400], fontWeight: '700' }]}>{item.compositeScore?.toFixed(1)}</Text>}
          palette={palette}
          onPress={() => rankingAnalytics.fighterOpened(item.fighter?.id)}
        />
      )}
      ListHeaderComponent={<Text style={[typography.headline, { color: palette.text.primary, padding: spacing.lg }]}>Pound for Pound</Text>}
    />
  );
}

// ── Division View ──
function DivisionView({ palette }: any) {
  const [division, setDivision] = useState('Heavyweight');
  const { data, isLoading, refetch } = useDivisionRankings(division);
  return (
    <View style={{ flex: 1 }}>
      <FlatList horizontal data={WEIGHT_CLASSES as readonly string[]} showsHorizontalScrollIndicator={false}
        contentContainerStyle={s.chipRow} keyExtractor={(d) => d}
        renderItem={({ item }) => (
          <TouchableOpacity onPress={() => setDivision(item)} style={[s.chip, { backgroundColor: division === item ? palette.primary[500] : palette.surface.card, borderColor: palette.surface.border }]}>
            <Text style={[typography.bodySmall, { color: division === item ? '#FFF' : palette.text.secondary, fontWeight: '600' }]}>{item}</Text>
          </TouchableOpacity>
        )}
      />
      <FlatList
        data={data?.rankings ?? []}
        keyExtractor={(r) => r.id}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} />}
        ListHeaderComponent={
          data?.champion ? (
            <View style={[s.championBanner, { backgroundColor: '#F59E0B20', borderColor: '#F59E0B40' }]}>
              <Text style={[typography.overline, { color: '#F59E0B' }]}>👑 Champion</Text>
              <Text style={[typography.title, { color: palette.text.primary }]}>{data.champion.fullName}</Text>
              <Text style={[typography.caption, { color: palette.text.secondary }]}>{data.champion.record}</Text>
            </View>
          ) : null
        }
        renderItem={({ item }) => (
          <RankingCard
            rank={item.rank} previousRank={item.previousRank} movement={item.movement}
            fighter={item.fighter} subtitle={item.fighter?.record}
            palette={palette}
          />
        )}
      />
    </View>
  );
}

// ── GOAT View ──
function GOATView({ palette }: any) {
  const { data, isLoading, refetch } = useGOAT();
  return (
    <FlatList
      data={data ?? []}
      keyExtractor={(g) => g.fighter?.id || String(g.rank)}
      refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} />}
      ListHeaderComponent={<Text style={[typography.headline, { color: palette.text.primary, padding: spacing.lg }]}>🐐 Greatest of All Time</Text>}
      renderItem={({ item }) => (
        <RankingCard
          rank={item.rank} movement="steady"
          fighter={item.fighter}
          subtitle={`Peak Elo: ${Math.round(item.eloPeak)} • ${item.titleDefenses} defenses • ${item.era}`}
          extra={<View style={[s.compositeBadge, { backgroundColor: palette.primary[500] }]}><Text style={[styles.mono, { color: '#FFF', fontWeight: '700' }]}>{item.compositeScore?.toFixed(1)}</Text></View>}
          palette={palette}
        />
      )}
    />
  );
}

// ── Prospects View ──
function ProspectsView({ palette }: any) {
  const { data, isLoading, refetch } = useProspects();
  return (
    <FlatList
      data={data ?? []}
      keyExtractor={(p) => p.fighter?.id}
      refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} />}
      ListHeaderComponent={<Text style={[typography.headline, { color: palette.text.primary, padding: spacing.lg }]}>🌟 Top Prospects</Text>}
      renderItem={({ item }) => (
        <RankingCard
          rank={null} movement="new"
          fighter={item.fighter}
          subtitle={`${item.record} • ${Math.round(item.finishRate * 100)}% finish • Age ${item.age}`}
          extra={
            <View style={{ flexDirection: 'row', gap: 8 }}>
              <View style={[s.prospectBadge, { backgroundColor: item.trajectory === 'rising' ? '#10B981' : '#F59E0B' }]}>
                <Text style={[styles.mono, { color: '#FFF', fontSize: 11 }]}>{item.trajectory}</Text>
              </View>
              <Text style={[styles.mono, { color: palette.text.tertiary }]}>{item.comparable ? `Like ${item.comparable}` : ''}</Text>
            </View>
          }
          palette={palette}
        />
      )}
    />
  );
}

// ── Movement View ──
function MovementView({ palette }: any) {
  const { data, isLoading, refetch } = useRankingMovement();
  return (
    <FlatList
      data={data ?? []}
      keyExtractor={(m, i) => `${m.fighter?.id}-${i}`}
      refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} />}
      ListHeaderComponent={<Text style={[typography.headline, { color: palette.text.primary, padding: spacing.lg }]}>📈 Biggest Movers</Text>}
      renderItem={({ item }) => (
        <RankingCard
          rank={item.toRank} previousRank={item.fromRank} movement={item.change > 0 ? 'up' : 'down'}
          fighter={item.fighter}
          subtitle={`${item.division} • ${item.fromRank} → ${item.toRank} • ${item.reason}`}
          palette={palette}
        />
      )}
    />
  );
}

// ── Ranking History Screen ──
export function RankingHistoryScreen({ route }: any) {
  const { fighterId, fighterName } = route.params;
  const { palette } = useTheme();
  const { data: history } = useRankingHistory(fighterId);
  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
        <Text style={[typography.headline, { color: palette.text.primary }]}>{fighterName}</Text>
        <Text style={[typography.body, { color: palette.text.secondary, marginBottom: spacing.xl }]}>Rank History</Text>
        <View style={[s.chartPlaceholder, { backgroundColor: '#1A1A2E', height: 200, borderRadius: radius.lg, marginBottom: spacing.xl }]}>
          <Text style={{ color: '#6B7280' }}>Rank Chart</Text>
        </View>
        {(history ?? []).map((point: RankingHistoryPoint, i: number) => (
          <View key={i} style={[s.historyRow, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <Text style={[typography.bodySmall, { color: palette.text.primary, fontWeight: '600' }]}>{point.date?.slice(0, 10)}</Text>
            <Text style={[styles.mono, { color: palette.primary[400] }]}>{point.rank ? `#${point.rank}` : point.isChampion ? '👑' : 'NR'}</Text>
            {point.event && <Text style={[typography.caption, { color: palette.text.tertiary }]}>{point.event}</Text>}
            {point.result && <Text style={[typography.caption, { color: point.result === 'W' ? '#10B981' : '#EF4444' }]}>{point.result}</Text>}
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

// ── Champion History Screen ──
export function ChampionHistoryScreen({ route }: any) {
  const { palette } = useTheme();
  const { data: champions } = useChampions();
  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <FlatList
        data={champions as any[] ?? []}
        keyExtractor={(c: any) => c.fighter?.id || Math.random().toString()}
        ListHeaderComponent={<Text style={[typography.headline, { color: palette.text.primary, padding: spacing.lg }]}>Champion History</Text>}
        renderItem={({ item }) => (
          <View style={[s.champRow, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{item.fighter?.fullName || item.fighter?.lastName}</Text>
            <Text style={[typography.caption, { color: palette.text.secondary }]}>{item.weightClass} • {item.defenses} defenses • {item.reign} days</Text>
          </View>
        )}
      />
    </SafeAreaView>
  );
}

// ── Title Defenses Screen ──
export function TitleDefensesScreen() {
  const { palette } = useTheme();
  const { data } = useTitleDefenses();
  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <FlatList
        data={data as any[] ?? []}
        keyExtractor={(d: any, i: number) => d?.fighter?.id ?? String(i)}
        ListHeaderComponent={<Text style={[typography.headline, { color: palette.text.primary, padding: spacing.lg }]}>Title Defenses</Text>}
        renderItem={({ item }) => (
          <View style={[s.defenseRow, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{item?.fighter?.fullName || item?.fighter?.lastName}</Text>
            <Text style={[styles.mono, { color: '#F59E0B', fontWeight: '700' }]}>{item?.defenses ?? item?.titleDefenses}</Text>
          </View>
        )}
      />
    </SafeAreaView>
  );
}

// Placeholder screens
export const PoundForPoundScreen = P4PView;
export const DivisionRankingsScreen = DivisionView;
export const RankMovementScreen = MovementView;
export const GOATRankingsScreen = GOATView;
export const ProspectsScreen = ProspectsView;
export const CompareRankingsScreen = () => <SafeAreaView style={[s.root, { backgroundColor: '#0A0A0A' }]}><Text style={{ color: '#9CA3AF', padding: 20 }}>Compare rankings coming soon</Text></SafeAreaView>;

const s = StyleSheet.create({
  root: { flex: 1 },
  header: { flexDirection: 'row', borderBottomWidth: 0.5 },
  viewTab: { flex: 1, paddingVertical: 14, alignItems: 'center' },
  chipRow: { paddingHorizontal: spacing.lg, paddingVertical: spacing.md, gap: 8 },
  chip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, borderWidth: 1 },
  championBanner: { margin: spacing.lg, padding: spacing.lg, borderRadius: radius.lg, borderWidth: 1, alignItems: 'center' },
  chartPlaceholder: { alignItems: 'center', justifyContent: 'center' },
  historyRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: spacing.md, borderRadius: radius.sm, borderWidth: 0.5, marginBottom: 4 },
  champRow: { padding: spacing.md, marginHorizontal: spacing.lg, borderRadius: radius.md, borderWidth: 0.5, marginBottom: 6 },
  defenseRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: spacing.md, marginHorizontal: spacing.lg, borderRadius: radius.md, borderWidth: 0.5, marginBottom: 6 },
  compositeBadge: { width: 52, height: 44, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  prospectBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 8 },
});

const styles = StyleSheet.create({ mono: { fontFamily: 'monospace', fontSize: 14 } });
