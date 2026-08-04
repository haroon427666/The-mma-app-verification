/** Fighters theme, accessibility, images, constants */

import React from 'react';
import { View, Text, Image } from 'react-native';

// ── Theme tokens ──
export const fighterColors = {
  win: '#10B981', loss: '#EF4444', draw: '#F59E0B', nc: '#6B7280',
  champion: '#F59E0B', interimChampion: '#FCD34D',
  streak: { hot: '#EF4444', warm: '#F97316', cold: '#10B981' },
  style: { striker: '#EF4444', grappler: '#8B5CF6', mixed: '#3B82F6', bjj: '#10B981' },
} as const;

// ── Accessibility ──
export const fighterLabels = {
  card: (name: string) => `Fighter: ${name}`,
  profile: (name: string, record: string) => `Profile for ${name}, record ${record}`,
  favorite: (name: string) => `${name} is one of your favorites`,
  unfavorite: (name: string) => `Remove ${name} from favorites`,
};

// ── Images ──
export function FighterAvatar({ uri, size = 48 }: { uri?: string | null; size?: number }) {
  return (
    <View style={{ width: size, height: size, borderRadius: size / 2, backgroundColor: '#1E1E32', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
      {uri ? <Image source={{ uri }} style={{ width: size, height: size, borderRadius: size / 2 }} /> : <Text style={{ fontSize: size / 2.5 }}>🥊</Text>}
    </View>
  );
}

// ── Constants ──
export const WEIGHT_CLASSES = ['Heavyweight','Light Heavyweight','Middleweight','Welterweight','Lightweight','Featherweight','Bantamweight','Flyweight',"Women's Bantamweight","Women's Flyweight","Women's Strawweight"] as const;
