/** Recommendations Screens + Theme + Charts + Errors */

import React from 'react';
import { View, Text, ScrollView, FlatList, TouchableOpacity, StyleSheet, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '@/hooks/useTheme';
import { typography, spacing, radius, shadows } from '@/theme';
import { useRecommendationsDashboard, useBecauseYouFollow, useBecauseYouWatched, useTrendingRecs, useHiddenGems, useDismissRecommendation, useRecommendationFeedback, useRecommendationStore, recommendationActions, recommendationAnalytics } from '../api';
import type { Recommendation, RecommendationsDashboard, RecommendationCategory } from '../types';

// ── CATEGORIES ──
const CATEGORIES: { key: RecommendationCategory; label: string; icon: string }[] = [
  { key: 'for_you', label: 'For You', icon: '🎯' },
  { key: 'because_you_follow', label: 'Following', icon: '👤' },
  { key: 'because_you_watched', label: 'Watched', icon: '👀' },
  { key: 'trending', label: 'Trending', icon: '🔥' },
  { key: 'similar', label: 'Similar', icon: '🔄' },
  { key: 'hidden_gems', label: 'Hidden Gems', icon: '💎' },
];

// ── Main Screen ──
export function RecommendationsScreen({ navigation }: any) {
  const { palette } = useTheme();
  const { category } = useRecommendationStore();
  const { data: dashboard, isLoading, refetch } = useRecommendationsDashboard();

  return (
    <SafeAreaView style={[s.root, { backgroundColor: palette.surface.bg }]}>
      <View style={[s.header, { borderBottomColor: palette.surface.border }]}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.chipRow}>
          {CATEGORIES.map((c) => (
            <TouchableOpacity key={c.key} onPress={() => { recommendationActions.setCategory(c.key); recommendationAnalytics.categoryViewed(c.key); }}
              style={[s.chip, { backgroundColor: category === c.key ? palette.primary[500] : palette.surface.card, borderColor: palette.surface.border }]}>
              <Text style={[typography.bodySmall, { color: category === c.key ? '#FFF' : palette.text.secondary, fontWeight: '600' }]}>{c.icon} {c.label}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      <ScrollView refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor={palette.primary[400]} />}>
        {category === 'for_you' && <ForYouSection dashboard={dashboard} palette={palette} navigation={navigation} />}
        {category === 'because_you_follow' && <BecauseFollowSection palette={palette} />}
        {category === 'because_you_watched' && <BecauseWatchedSection palette={palette} />}
        {category === 'trending' && <TrendingSection palette={palette} />}
        {category === 'hidden_gems' && <HiddenGemsSection palette={palette} />}
        {category === 'similar' && <SimilarSection dashboard={dashboard} palette={palette} />}
      </ScrollView>
    </SafeAreaView>
  );
}

// ── For You Section ──
function ForYouSection({ dashboard, palette, navigation }: { dashboard?: RecommendationsDashboard; palette: any; navigation: any }) {
  if (!dashboard) return null;
  return (
    <View style={{ paddingTop: spacing.lg }}>
      {dashboard.forYou && dashboard.forYou.length > 0 && (
        <RecSectionCarousel title="🎯 For You" items={dashboard.forYou} palette={palette} />
      )}
      {dashboard.becauseYouFollow && dashboard.becauseYouFollow.length > 0 && (
        <RecSectionRow title="👤 Because You Follow" items={dashboard.becauseYouFollow} palette={palette} />
      )}
      {dashboard.becauseYouWatched && dashboard.becauseYouWatched.length > 0 && (
        <RecSectionRow title="👀 Because You Watched" items={dashboard.becauseYouWatched} palette={palette} />
      )}
      {dashboard.trending && dashboard.trending.length > 0 && (
        <RecSectionCarousel title="🔥 Trending" items={dashboard.trending} palette={palette} />
      )}
      {dashboard.similarFighters && dashboard.similarFighters.length > 0 && (
        <RecSectionRow title="🔄 Similar to Your Favorites" items={dashboard.similarFighters} palette={palette} />
      )}
      {dashboard.hiddenGems && dashboard.hiddenGems.length > 0 && (
        <RecSectionRow title="💎 Hidden Gems" items={dashboard.hiddenGems} palette={palette} />
      )}
      <View style={{ height: 60 }} />
    </View>
  );
}

function BecauseFollowSection({ palette }: any) {
  const { data } = useBecauseYouFollow();
  return <RecList data={data ?? []} palette={palette} emptyMsg="Follow fighters to get personalized recommendations." />;
}

function BecauseWatchedSection({ palette }: any) {
  const { data } = useBecauseYouWatched();
  return <RecList data={data ?? []} palette={palette} emptyMsg="Watch more events for personalized picks." />;
}

function TrendingSection({ palette }: any) {
  const { data } = useTrendingRecs();
  return <RecList data={data as Recommendation[] ?? []} palette={palette} />;
}

function HiddenGemsSection({ palette }: any) {
  const { data } = useHiddenGems();
  return <RecList data={data as Recommendation[] ?? []} palette={palette} emptyMsg="No hidden gems right now. Check back later." />;
}

function SimilarSection({ dashboard, palette }: any) {
  const items = dashboard?.similarFighters ?? [];
  return <RecList data={items} palette={palette} />;
}

// ── Reusable Section Components ──
function RecSectionCarousel({ title, items, palette }: { title: string; items: Recommendation[]; palette: any }) {
  return (
    <View style={s.section}>
      <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: spacing.md }]}>{title}</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 12, paddingRight: spacing.lg }}>
        {items.map((item) => <RecommendationCard key={item.id} item={item} palette={palette} />)}
      </ScrollView>
    </View>
  );
}

function RecSectionRow({ title, items, palette }: { title: string; items: Recommendation[]; palette: any }) {
  return (
    <View style={s.section}>
      <Text style={[typography.subtitle, { color: palette.text.primary, marginBottom: spacing.sm }]}>{title}</Text>
      {items.map((item) => <RecommendationRow key={item.id} item={item} palette={palette} />)}
    </View>
  );
}

function RecList({ data, palette, emptyMsg }: { data: Recommendation[]; palette: any; emptyMsg?: string }) {
  if (data.length === 0) return <Text style={[typography.body, { color: palette.text.secondary, textAlign: 'center', padding: spacing.xxxl }]}>{emptyMsg || 'No recommendations yet'}</Text>;
  return (
    <View style={s.section}>
      {data.map((item) => <RecommendationRow key={item.id} item={item} palette={palette} />)}
    </View>
  );
}

// ── Cards ──
function RecommendationCard({ item, palette }: { item: Recommendation; palette: any }) {
  const feed = useRecommendationFeedback();
  const dismiss = useDismissRecommendation();
  return (
    <View style={[s.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <TouchableOpacity onPress={() => dismiss.mutate(item.entityId)} style={s.dismissBtn}>
        <Text style={[typography.caption, { color: palette.text.tertiary }]}>✕</Text>
      </TouchableOpacity>
      <Text style={[typography.bodySmall, { color: palette.primary[400], textTransform: 'uppercase', fontWeight: '700' }]}>{item.type}</Text>
      <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600', marginTop: 4 }]} numberOfLines={2}>{item.name}</Text>
      {item.subtitle && <Text style={[typography.caption, { color: palette.text.secondary, marginTop: 2 }]}>{item.subtitle}</Text>}
      <View style={s.reasonWrap}>
        {item.reasons?.filter((r) => r.weight > 0.3).slice(0, 3).map((r, i) => (
          <View key={i} style={[s.reasonPill, { backgroundColor: palette.surface.elevated }]}>
            <Text style={[typography.caption, { color: palette.text.secondary }]}>{r.reason}</Text>
          </View>
        ))}
      </View>
      <View style={s.feedbackRow}>
        <TouchableOpacity onPress={() => feed.mutate({ entityId: item.entityId, helpful: true })}>
          <Text style={[typography.caption, { color: '#10B981', marginRight: 12 }]}>👍</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => feed.mutate({ entityId: item.entityId, helpful: false })}>
          <Text style={[typography.caption, { color: '#EF4444' }]}>👎</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

function RecommendationRow({ item, palette }: { item: Recommendation; palette: any }) {
  return (
    <View style={[s.row, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
      <View style={{ flex: 1 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <Text style={[typography.bodySmall, { color: palette.primary[400], textTransform: 'uppercase', fontWeight: '700', marginRight: 6 }]}>{item.type}</Text>
          <View style={[s.scoreDot, { backgroundColor: item.score > 0.8 ? '#10B981' : item.score > 0.6 ? '#F59E0B' : '#6B7280' }]} />
        </View>
        <Text style={[typography.body, { color: palette.text.primary, fontWeight: '600', marginTop: 2 }]}>{item.name}</Text>
        <View style={s.reasonWrap}>
          {item.reasons?.slice(0, 2).map((r, i) => (
            <View key={i} style={[s.reasonPill, { backgroundColor: palette.surface.elevated }]}>
              <Text style={[typography.caption, { color: palette.text.secondary }]}>{r.reason}</Text>
            </View>
          ))}
        </View>
      </View>
      <View style={[s.scoreBadge, { backgroundColor: item.score > 0.8 ? '#10B98120' : palette.surface.elevated }]}>
        <Text style={[typography.mono, { color: item.score > 0.8 ? '#10B981' : palette.text.tertiary, fontWeight: '700' }]}>{Math.round(item.score * 100)}</Text>
      </View>
    </View>
  );
}

export { RecommendationsScreen as RecommendationDetailScreen };

// ── Theme / Charts / Errors ──
export const recommendationColors = {
  score: { high: '#10B981', medium: '#F59E0B', low: '#6B7280' },
  signal: { collaborative: '#3B82F6', content_based: '#8B5CF6', trending: '#EF4444', hidden_gem: '#F59E0B' },
} as const;

export function MetricsChart({ metrics }: { metrics: any }) {
  if (!metrics) return null;
  return (
    <View style={{ margin: spacing.lg, padding: spacing.lg, borderRadius: radius.lg, backgroundColor: '#1A1A2E' }}>
      <Text style={[typography.subtitle, { color: '#FFF', marginBottom: spacing.md }]}>Recommendation Quality</Text>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, justifyContent: 'center' }}>
        {[{ l: 'Precision@K', v: metrics.precisionAtK?.[5] ?? metrics.precisionAtK }, { l: 'Recall', v: metrics.recallAtK?.[5] ?? metrics.recallAtK }, { l: 'NDCG', v: metrics.ndcg }, { l: 'MRR', v: metrics.mrr }, { l: 'Coverage', v: metrics.coverage }, { l: 'Diversity', v: metrics.diversity }].map(({ l, v }) => (
          <View key={l} style={{ padding: spacing.md, alignItems: 'center', minWidth: 80 }}>
            <Text style={[typography.title, { color: '#3B82F6' }]}>{typeof v === 'number' ? v.toFixed(2) : '--'}</Text>
            <Text style={[typography.caption, { color: '#9CA3AF' }]}>{l}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

export function NoRecommendations() {
  return <View style={{ alignItems: 'center', padding: 60 }}><Text style={{ fontSize: 48 }}>🎯</Text><Text style={{ color: '#9CA3AF', marginTop: 12 }}>No recommendations yet. Follow fighters and watch events to personalize your feed.</Text></View>;
}

const s = StyleSheet.create({
  root: { flex: 1 },
  header: { borderBottomWidth: 0.5, paddingVertical: spacing.md },
  chipRow: { paddingHorizontal: spacing.lg, gap: 8 },
  chip: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, borderWidth: 1 },
  section: { paddingHorizontal: spacing.lg, marginBottom: spacing.xl },
  card: { width: 220, padding: spacing.lg, borderRadius: radius.lg, borderWidth: 0.5, marginRight: 12, ...shadows.sm },
  dismissBtn: { position: 'absolute', top: spacing.sm, right: spacing.sm, padding: 4, zIndex: 1 },
  row: { flexDirection: 'row', alignItems: 'center', padding: spacing.md, marginBottom: 6, borderRadius: radius.md, borderWidth: 0.5, marginHorizontal: spacing.lg },
  reasonWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 4, marginTop: 6 },
  reasonPill: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 10 },
  scoreDot: { width: 8, height: 8, borderRadius: 4 },
  scoreBadge: { width: 42, height: 42, borderRadius: 21, alignItems: 'center', justifyContent: 'center' },
  feedbackRow: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: spacing.md },
});
