/** Recommendations screen — "For You" feed */

import React from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { useTheme } from '@/hooks/useTheme';
import api from '@/services/api';
import { typography, spacing, radius } from '@/theme';
import type { Recommendation } from '@/features/models';

export function RecommendationsScreen({ navigation }: any) {
  const { palette } = useTheme();
  const { data } = useQuery<Recommendation[]>({
    queryKey: ['recommendations'],
    queryFn: async () => { const { data } = await api.get('/v1/recommendations?limit=20'); return data.data ?? []; },
    staleTime: 5 * 60 * 1000,
  });

  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <FlatList
        data={data ?? []}
        keyExtractor={(r) => r.id}
        ListHeaderComponent={<Text style={[typography.headline, { color: palette.text.primary, padding: spacing.lg }]}>For You</Text>}
        renderItem={({ item }) => (
          <TouchableOpacity style={[s.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            <View style={{ flex: 1 }}>
              <Text style={[typography.bodySmall, { color: palette.primary[400], textTransform: 'uppercase', fontWeight: '700' }]}>{item.type}</Text>
              <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600', marginTop: 4 }]}>{item.name}</Text>
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 6, gap: 4 }}>
                {item.reasons.slice(0, 3).map((r, i) => (
                  <View key={i} style={[s.reasonPill, { backgroundColor: palette.surface.elevated }]}>
                    <Text style={[typography.caption, { color: palette.text.secondary }]}>{r}</Text>
                  </View>
                ))}
              </View>
            </View>
            <View style={[s.scoreBadge, { backgroundColor: palette.primary[500] }]}>
              <Text style={[typography.caption, { color: '#FFF', fontWeight: '700' }]}>{Math.round(item.score * 100)}</Text>
            </View>
          </TouchableOpacity>
        )}
      />
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  card: { flexDirection: 'row', padding: spacing.md, marginHorizontal: spacing.lg, marginBottom: 8, borderRadius: radius.md, borderWidth: 0.5 },
  reasonPill: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 10 },
  scoreBadge: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center', marginLeft: 12 },
});
