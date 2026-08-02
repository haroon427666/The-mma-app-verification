/** Images — CachedImage, FighterAvatar, CountryFlag, Poster, PromotionLogo */
import React, { useState } from 'react';
import { View, Image, StyleSheet, Text } from 'react-native';
import { spacing, radius } from '@/theme';

export function CachedImage({ uri, style, fallback }: { uri?: string | null; style?: any; fallback?: string }) {
  const [error, setError] = useState(false);
  if (!uri || error) {
    return (
      <View style={[s.fallback, style, { backgroundColor: '#1E1E32' }]}>
        <Text style={{ fontSize: style?.width ? Math.min(style.width / 3, 40) : 24 }}>{fallback || '🥊'}</Text>
      </View>
    );
  }
  return <Image source={{ uri }} style={style} onError={() => setError(true)} resizeMode="cover" />;
}

export function FighterAvatar({ uri, size = 48, name }: { uri?: string | null; size?: number; name?: string }) {
  return (
    <View style={[s.avatar, { width: size, height: size, borderRadius: size / 2, backgroundColor: '#1E1E32' }]}>
      {uri ? <Image source={{ uri }} style={{ width: size, height: size, borderRadius: size / 2 }} /> : (
        <Text style={{ fontSize: size / 2.5 }}>🥊</Text>
      )}
    </View>
  );
}

export function CountryFlag({ code, size = 20 }: { code?: string; size?: number }) {
  if (!code) return null;
  return (
    <View style={[s.flag, { width: size * 1.5, height: size, backgroundColor: '#1E1E32', borderRadius: 2 }]}>
      <Text style={{ fontSize: size * 0.7 }}>{code.toUpperCase().slice(0, 2)}</Text>
    </View>
  );
}

export function Poster({ uri, style }: { uri?: string | null; style?: any }) {
  if (!uri) return <View style={[s.poster, style, { backgroundColor: '#1E1E32' }]}><Text>🥊</Text></View>;
  return <Image source={{ uri }} style={[s.poster, style]} resizeMode="cover" />;
}

export function PromotionLogo({ uri, name, size = 24 }: { uri?: string | null; name: string; size?: number }) {
  return (
    <View style={[s.logo, { height: size, borderRadius: 4, backgroundColor: '#1A1A2E' }]}>
      {uri ? <Image source={{ uri }} style={{ width: size * 2, height: size }} resizeMode="contain" /> : (
        <Text style={[s.logoText, { fontSize: size * 0.45 }]}>{name}</Text>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  fallback: { alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  avatar: { alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  flag: { alignItems: 'center', justifyContent: 'center' },
  poster: { width: '100%', aspectRatio: 16 / 9, borderRadius: radius.lg, alignItems: 'center', justifyContent: 'center' },
  logo: { paddingHorizontal: spacing.sm, alignItems: 'center', justifyContent: 'center' },
  logoText: { color: '#9CA3AF', fontWeight: '700' },
});
