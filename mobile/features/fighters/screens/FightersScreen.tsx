/** Fighter screens — list, detail with tabs */

import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, FlatList, StyleSheet, RefreshControl, Dimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { useTheme } from '@/hooks/useTheme';
import api from '@/services/api';
import { typography, spacing, radius, shadows } from '@/theme';
import type { Fighter } from '@/features/models';

export function FightersScreen({ navigation }: any) {
  const { palette } = useTheme();
  const [division, setDivision] = useState<string | null>(null);
  const { data, isLoading, refetch } = useQuery<Fighter[]>({
    queryKey: ['fighters', division],
    queryFn: async () => {
      const url = division ? `/v1/fighters?weight_class=${division}&limit=50` : '/v1/fighters?limit=50';
      const { data } = await api.get(url);
      return data.data ?? [];
    },
    staleTime: 10 * 60 * 1000,
  });

  const divisions = ['Heavyweight','Light Heavyweight','Middleweight','Welterweight','Lightweight','Featherweight','Bantamweight','Flyweight','Women\'s Bantamweight','Women\'s Flyweight','Women\'s Strawweight'];

  return (
    <SafeAreaView style={[st.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={st.chipRow} contentContainerStyle={{ paddingHorizontal: spacing.lg, gap: 8 }}>
        <TouchableOpacity onPress={() => setDivision(null)} style={[st.chip, { backgroundColor: !division ? palette.primary[500] : palette.surface.card, borderColor: palette.surface.border }]}>
          <Text style={[typography.bodySmall, { color: !division ? '#FFF' : palette.text.secondary, fontWeight: '600' }]}>All</Text>
        </TouchableOpacity>
        {divisions.map((d) => (
          <TouchableOpacity key={d} onPress={() => setDivision(d)} style={[st.chip, { backgroundColor: division === d ? palette.primary[500] : palette.surface.card, borderColor: palette.surface.border }]}>
            <Text style={[typography.bodySmall, { color: division === d ? '#FFF' : palette.text.secondary, fontWeight: '600' }]}>{d}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
      <FlatList
        data={data ?? []}
        keyExtractor={(f) => f.id}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor={palette.primary[400]} />}
        renderItem={({ item }) => <FighterRow fighter={item} palette={palette} onPress={() => navigation.navigate('fighterDetail', { id: item.id })} />}
      />
    </SafeAreaView>
  );
}

function FighterRow({ fighter, palette, onPress }: { fighter: Fighter; palette: any; onPress: () => void }) {
  return (
    <TouchableOpacity onPress={onPress} style={[st.row, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <View style={[st.avatar, { backgroundColor: palette.surface.elevated }]}><Text style={{ fontSize: 22 }}>🥊</Text></View>
      <View style={{ flex: 1, marginLeft: 12 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{fighter.fullName || fighter.lastName}</Text>
          {fighter.isChampion && <Text style={{ marginLeft: 4 }}>👑</Text>}
        </View>
        <Text style={[typography.caption, { color: palette.text.secondary }]}>{fighter.record} • {fighter.weightClass}</Text>
        {fighter.streak > 0 && <Text style={[typography.caption, { color: '#10B981' }]}>W{fighter.streak} streak</Text>}
      </View>
      <View style={{ alignItems: 'flex-end' }}>
        {fighter.latestRank && <Text style={[typography.title, { color: '#F59E0B' }]}>#{fighter.latestRank}</Text>}
        {fighter.eloRating && <Text style={[typography.mono, { color: palette.text.tertiary }]}>{Math.round(fighter.eloRating)}</Text>}
      </View>
    </TouchableOpacity>
  );
}

export function FighterDetailScreen({ route }: any) {
  const { palette } = useTheme();
  const [tab, setTab] = useState(0);
  const { id } = route.params;
  const { data: fighter, isLoading } = useQuery({
    queryKey: ['fighter', id],
    queryFn: async () => { const { data } = await api.get(`/v1/fighters/${id}`); return data.data as Fighter; },
  });

  if (isLoading || !fighter) return <View style={[st.root, { backgroundColor: palette.surface.bg }]} />;

  const tabs = ['Overview', 'Stats', 'History'];

  return (
    <SafeAreaView style={[st.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView>
        <View style={[st.banner, { backgroundColor: palette.surface.card }]}>
          <View style={[st.avatarLg, { backgroundColor: palette.surface.elevated }]}><Text style={{ fontSize: 40 }}>🥊</Text></View>
          <Text style={[typography.headline, { color: palette.text.primary, marginTop: 12 }]}>{fighter.fullName || `${fighter.firstName} ${fighter.lastName}`}</Text>
          {fighter.nickname && <Text style={[typography.body, { color: palette.text.secondary }]}>"{fighter.nickname}"</Text>}
          <Text style={[typography.title, { color: palette.primary[400], marginTop: 8 }]}>{fighter.record}</Text>
          <View style={st.statGrid}>
            <StatBox label="Division" value={fighter.weightClass || '-'} palette={palette} />
            <StatBox label="Rank" value={fighter.isChampion ? '👑 Champ' : fighter.latestRank ? `#${fighter.latestRank}` : 'NR'} palette={palette} />
            <StatBox label="Elo" value={fighter.eloRating ? String(Math.round(fighter.eloRating)) : '-'} palette={palette} />
            <StatBox label="Finish Rate" value={`${Math.round((fighter.finishRate ?? 0) * 100)}%`} palette={palette} />
          </View>
        </View>

        <View style={st.tabRow}>
          {tabs.map((t, i) => (
            <TouchableOpacity key={t} onPress={() => setTab(i)} style={[st.tab, tab === i && { borderBottomColor: palette.primary[400], borderBottomWidth: 2 }]}>
              <Text style={[typography.body, { color: tab === i ? palette.primary[400] : palette.text.tertiary, fontWeight: '600' }]}>{t}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {tab === 0 && <OverviewTab fighter={fighter} palette={palette} />}
        {tab === 1 && <StatsTab fighter={fighter} palette={palette} />}
        {tab === 2 && <HistoryTab fighter={fighter} palette={palette} />}
      </ScrollView>
    </SafeAreaView>
  );
}

function StatBox({ label, value, palette }: any) {
  return (
    <View style={[st.statBox, { backgroundColor: palette.surface.elevated }]}>
      <Text style={[typography.title, { color: palette.text.primary, fontWeight: '700' }]}>{value}</Text>
      <Text style={[typography.caption, { color: palette.text.tertiary }]}>{label}</Text>
    </View>
  );
}

function OverviewTab({ fighter, palette }: any) {
  return (
    <View style={{ padding: spacing.lg }}>
      <StatRow label="Age" value={fighter.age ? `${fighter.age}` : '-'} palette={palette} />
      <StatRow label="Height" value={fighter.heightCm ? `${fighter.heightCm} cm` : '-'} palette={palette} />
      <StatRow label="Reach" value={fighter.reachCm ? `${fighter.reachCm} cm` : '-'} palette={palette} />
      <StatRow label="Stance" value={fighter.stance || '-'} palette={palette} />
      <StatRow label="Team" value={fighter.team || '-'} palette={palette} />
    </View>
  );
}

function StatRow({ label, value, palette }: { label: string; value: string; palette: any }) {
  return (
    <View style={st.statRow}>
      <Text style={[typography.body, { color: palette.text.secondary }]}>{label}</Text>
      <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{value}</Text>
    </View>
  );
}

function StatsTab({ fighter, palette }: any) {
  const s = fighter.stats;
  if (!s) return <Text style={[typography.body, { color: palette.text.secondary, textAlign: 'center', padding: 40 }]}>No detailed stats available</Text>;
  return (
    <View style={{ padding: spacing.lg }}>
      <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: 12 }]}>Striking</Text>
      <StatRow label="Sig. Strikes/min" value={`${s.sigStrikesLandedPerMin?.toFixed(1)}`} palette={palette} />
      <StatRow label="Accuracy" value={`${s.sigStrikesAccuracyPct?.toFixed(0)}%`} palette={palette} />
      <StatRow label="Defense" value={`${s.sigStrikesDefensePct?.toFixed(0)}%`} palette={palette} />
      <Text style={[typography.subtitle, { color: palette.text.primary, marginTop: 20, marginBottom: 12 }]}>Grappling</Text>
      <StatRow label="Takedowns/15" value={`${s.takedownAvgPer15?.toFixed(1)}`} palette={palette} />
      <StatRow label="TD Accuracy" value={`${s.takedownAccuracyPct?.toFixed(0)}%`} palette={palette} />
      <StatRow label="TD Defense" value={`${s.takedownDefensePct?.toFixed(0)}%`} palette={palette} />
      <StatRow label="Subs/15" value={`${s.submissionAvgPer15?.toFixed(1)}`} palette={palette} />
    </View>
  );
}

function HistoryTab({ fighter, palette }: any) {
  const { data: fights } = useQuery({
    queryKey: ['fighterFights', fighter.id],
    queryFn: async () => { const { data } = await api.get(`/v1/fighters/${fighter.id}/fights`); return data.data ?? []; },
  });
  const fightsList = (fights ?? []) as any[];
  if (fightsList.length === 0) return <Text style={[typography.body, { color: palette.text.secondary, textAlign: 'center', padding: 40 }]}>No fight history</Text>;
  return (
    <View style={{ padding: spacing.lg }}>
      {fightsList.slice(0, 10).map((f: any, i: number) => {
        const won = f.winnerId === fighter.id;
        return (
          <View key={i} style={[st.historyRow, { borderLeftColor: won ? '#10B981' : '#EF4444', backgroundColor: palette.surface.card }]}>
            <Text style={[typography.bodySmall, { color: palette.text.primary, fontWeight: '600' }]}>{f.opponentName || f.fighterBName || f.fighterBName}</Text>
            <Text style={[typography.caption, { color: won ? '#10B981' : '#EF4444' }]}>{won ? 'W' : 'L'} {f.method || ''} {f.round ? `R${f.round}` : ''}</Text>
          </View>
        );
      })}
    </View>
  );
}

const st = StyleSheet.create({
  root: { flex: 1 },
  chipRow: { maxHeight: 48, marginVertical: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, borderWidth: 1 },
  row: { flexDirection: 'row', alignItems: 'center', padding: spacing.md, marginHorizontal: spacing.lg, marginBottom: 8, borderRadius: radius.md, borderWidth: 0.5 },
  avatar: { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center' },
  banner: { padding: spacing.xl, alignItems: 'center' },
  avatarLg: { width: 80, height: 80, borderRadius: 40, alignItems: 'center', justifyContent: 'center' },
  statGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', marginTop: spacing.lg, gap: 8 },
  statBox: { padding: spacing.md, borderRadius: radius.md, alignItems: 'center', minWidth: 80 },
  tabRow: { flexDirection: 'row', borderBottomWidth: 0.5, borderBottomColor: '#2A2A3E' },
  tab: { flex: 1, paddingVertical: 14, alignItems: 'center' },
  statRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 10, borderBottomWidth: 0.5, borderBottomColor: '#2A2A3E' },
  historyRow: { borderLeftWidth: 3, padding: spacing.md, borderRadius: radius.sm, marginBottom: 8 },
});
