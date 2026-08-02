/** WatchlistButton — toggle watchlist with visual feedback */
import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { typography, radius } from '@/theme';

export function WatchlistButton({ isWatched, onToggle, palette }: { isWatched: boolean; onToggle: () => void; palette: any }) {
  return (
    <TouchableOpacity onPress={onToggle} style={[s.btn, { backgroundColor: isWatched ? palette.primary[500] : palette.surface.card, borderColor: isWatched ? palette.primary[500] : palette.surface.border }]} accessibilityRole="button" accessibilityLabel={isWatched ? 'Remove from watchlist' : 'Add to watchlist'}>
      <Text style={[typography.bodySmall, { color: isWatched ? '#FFF' : palette.text.primary }]}>{isWatched ? '👁 Watching' : '+ Watch'}</Text>
    </TouchableOpacity>
  );
}
const s = StyleSheet.create({ btn: { flex: 1, paddingVertical: 12, borderRadius: radius.md, borderWidth: 1, alignItems: 'center' } });
