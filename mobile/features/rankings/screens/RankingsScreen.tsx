/** Rankings screen — P4P, men, women, by division */

import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { useTheme } from '@/hooks/useTheme';
import api from '@/services/api';
import { typography, spacing, radius } from '@/theme';
import type { Ranking } from '@/features/models';

export function RankingsScreen() {
  const { palette } = useTheme();
  const [division, setDivision] = useState('Pound for Pound');
  const divisions = ['Pound for Pound', 'Heavyweight', 'Light Heavyweight', 'Middleweight', 'Welterweight', 'Lightweight', 'Featherweight', 'Bantamweight', 'Flyweight', "Women's Bantamweight", "Women's Flyweight", "Women's Strawweight"];

  const { data, isLoading } = useQuery<Ranking[]>({
    queryKey: ['rankings', division],
    queryFn: async () => {
      const url = division === 'Pound for Pound' ? '/v1/rankings?type=p4p' : `/v1/rankings?weight_class=${encodeURIComponent(division)}`;
      const { data } = await api.get(url);
      return data.data ?? [];
    },
    staleTime: 10 * 60 * 1000,
  });

  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <View style={{ paddingHorizontal: spacing.lg, paddingVertical: spacing.md }}>
        <FlatList horizontal showsHorizontalScrollIndicator={false} data={divisions} keyExtractor={(d) => d}
          renderItem={({ item }) => (
            <TouchableOpacity onPress={() => setDivision(item)} style={[s.chip, { backgroundColor: division === item ? palette.primary[500] : palette.surface.card, borderColor: palette.surface.border }]}>
              <Text style={[typography.bodySmall, { color: division === item ? '#FFF' : palette.text.secondary, fontWeight: '600' }]}>{item}</Text>
            </TouchableOpacity>
          )}
        />
      </View>
      <FlatList data={data ?? []} keyExtractor={(r) => r.id}
        renderItem={({ item, index }) => (
          <View style={[s.rankRow, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <View style={[s.rankNum, { backgroundColor: index < 3 ? '#F59E0B' : palette.surface.elevated }]}>
              <Text style={[typography.title, { color: index < 3 ? '#FFF' : palette.text.secondary, fontWeight: '700' }]}>
                {item.isChampion ? '👑' : `#${item.rank}`}
              </Text>
            </View>
            <View style={{ flex: 1, marginLeft: 12 }}>
              <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600' }]}>{item.fighter?.fullName || item.fighter?.lastName}</Text>
              <Text style={[typography.caption, { color: palette.text.secondary }]}>{item.fighter?.record} • {item.weightClass}</Text>
            </View>
            {item.movement && item.movement !== 'steady' && (
              <Text style={[typography.bodySmall, { color: item.movement === 'up' ? '#10B981' : '#EF4444', fontWeight: '700' }]}>
                {item.movement === 'up' ? '▲' : '▼'} {item.previousRank && item.previousRank !== item.rank ? Math.abs(item.previousRank - item.rank) : ''}
              </Text>
            )}
          </View>
        )}
      />
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  chip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, borderWidth: 1, marginRight: 8 },
  rankRow: { flexDirection: 'row', alignItems: 'center', padding: spacing.md, marginHorizontal: spacing.lg, marginBottom: 6, borderRadius: radius.md, borderWidth: 0.5 },
  rankNum: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
});
