/** Detail sections — composed layout blocks for EventDetailScreen */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { typography, spacing, radius } from '@/theme';
import { Countdown } from '../components/Countdown';
import { FightCard } from '../components/FightCard';
import { FightPredictionCard } from '../components/FightPredictionCard';
import { VenueCard, BroadcastCard, SectionHeader } from '../components/SupportComponents';
import { Poster, PromotionLogo } from '../images';
import { LivePulse } from '../animations';
import { groupBySegment } from '../utils/fightSorter';

export function EventHero({ event, palette, live }: any) {
  return (
    <View style={s.section}>
      <Poster uri={event.bannerUrl || event.posterUrl} style={s.poster} />
      {live && <View style={{ marginTop: -30, alignItems: 'center' }}><LivePulse /></View>}
      <View style={s.row}>
        <PromotionLogo uri={event.promotionLogo} name={event.promotion} />
        <Text style={[typography.caption, { color: palette.text.tertiary }]}>{event.promotion}</Text>
      </View>
      <Text style={[typography.headline, { color: palette.text.primary, marginTop: 8 }]}>{event.name}</Text>
    </View>
  );
}

export function EventInformation({ event, palette }: any) {
  return (
    <View style={s.infoRow}>
      <Text style={[typography.caption, { color: palette.text.secondary }]}>
        {new Date(event.date || event.startTime).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
      </Text>
      <Text style={[typography.caption, { color: palette.text.tertiary }]}>
        {event.fightCount} fights
      </Text>
    </View>
  );
}

export function FightCardSection({ event, predictions, palette, onFightPress }: any) {
  const grouped = groupBySegment(event.fights ?? []);
  const order = ['main', 'co-main', 'mainCard', 'prelims', 'earlyPrelims'];
  return (
    <View style={s.section}>
      <SectionHeader title="Fight Card" count={event.fights?.length} palette={palette} />
      {order.map((seg) =>
        grouped[seg] ? (
          <FightCard key={seg} segment={seg} fights={grouped[seg]} predictions={predictions} palette={palette} onFightPress={onFightPress} />
        ) : null,
      )}
    </View>
  );
}

export function PredictionSection({ predictions, palette }: any) {
  if (!predictions || Object.keys(predictions).length === 0) return null;
  const first = Object.values(predictions)[0] as any;
  return <FightPredictionCard prediction={first} palette={palette} />;
}

export function BroadcastSection({ event, palette }: any) {
  if (!event.broadcasters?.length && !event.timezone) return null;
  return <BroadcastCard broadcasters={event.broadcasters || []} timezone={event.timezone} palette={palette} />;
}

export function VenueSection({ event, palette }: any) {
  const v = event.venue; if (!v && !event.city) return null;
  return <VenueCard venue={v || 'TBA'} city={event.city || ''} country={event.country || ''} palette={palette} />;
}

const s = StyleSheet.create({
  section: { paddingHorizontal: spacing.lg, marginBottom: spacing.xl },
  poster: { borderRadius: radius.lg, marginBottom: spacing.md },
  row: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: spacing.sm },
  infoRow: { flexDirection: 'row', justifyContent: 'space-between', paddingHorizontal: spacing.lg, marginBottom: spacing.md },
});
