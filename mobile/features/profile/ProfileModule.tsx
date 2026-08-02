/** Profile + Settings Modules — profile, stats, sessions, theme, data export, delete */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';
import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert, Switch } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useTheme } from '@/hooks/useTheme';
import { typography, spacing, radius } from '@/theme';

// ── Types ──
export interface UserProfile { id: string; email: string; username: string; displayName: string | null; avatarUrl: string | null; role: string; createdAt: string; }
export interface UserPrefs { theme: 'light' | 'dark' | 'amoled' | 'system'; language: string; timezone: string; units: 'metric' | 'imperial'; }
export interface UserSession { id: string; device: string; os: string; location: string | null; lastSeen: string; current: boolean; }
export interface UserStats { predictions: number; favorites: number; watchlist: number; accountAge: number; }

// ── API ──
export const profileApi = {
  me: () => api.get('/v1/me'),
  stats: () => api.get('/v1/me/stats'),
  sessions: () => api.get('/v1/me/sessions'),
  revokeSession: (id: string) => api.delete(`/v1/me/sessions/${id}`),
  revokeAll: () => api.delete('/v1/me/sessions'),
  preferences: () => api.get('/v1/me/preferences'),
  updatePreferences: (p: Partial<UserPrefs>) => api.patch('/v1/me/preferences', p),
  deleteAccount: () => api.delete('/v1/me'),
  exportData: () => api.get('/v1/me/export'),
  updateProfile: (d: any) => api.patch('/v1/me', d),
};

// ── Repository ──
export const profileRepo = {
  me: async () => { const { data } = await profileApi.me(); return (data?.data ?? data) as UserProfile; },
  stats: async () => { const { data } = await profileApi.stats(); return (data?.data ?? data) as UserStats; },
  sessions: async () => { const { data } = await profileApi.sessions(); return (data?.data ?? data) as UserSession[]; },
  revokeSession: async (id: string) => { await profileApi.revokeSession(id); },
  revokeAll: async () => { await profileApi.revokeAll(); },
  preferences: async () => { const { data } = await profileApi.preferences(); return (data?.data ?? data) as UserPrefs; },
  updatePreferences: async (p: Partial<UserPrefs>) => { await profileApi.updatePreferences(p); },
  deleteAccount: async () => { await profileApi.deleteAccount(); },
  exportData: async () => { const { data } = await profileApi.exportData(); return data; },
  updateProfile: async (d: any) => { await profileApi.updateProfile(d); },
};

// ── Services ──
export const profileKeys = { me: () => ['me'] as const, stats: () => ['me', 'stats'] as const, sessions: () => ['me', 'sessions'] as const, prefs: () => ['me', 'prefs'] as const };
export const profileCache = { stale: 5 * 60_000, sessionStale: 60_000 };

// ── Stores ──
export const useProfileStore = create<{ theme: string; developerMode: boolean; offlineMode: boolean }>(() => ({ theme: 'dark', developerMode: false, offlineMode: false }));
export const profileActions = {
  setTheme: (t: string) => useProfileStore.setState({ theme: t }),
  toggleDev: () => useProfileStore.setState((s) => ({ developerMode: !s.developerMode })),
  toggleOffline: () => useProfileStore.setState((s) => ({ offlineMode: !s.offlineMode })),
};

// ── Hooks ──
export function useProfile() { return useQuery<UserProfile>({ queryKey: profileKeys.me(), queryFn: profileRepo.me, staleTime: profileCache.stale }); }
export function useUserStats() { return useQuery<UserStats>({ queryKey: profileKeys.stats(), queryFn: profileRepo.stats, staleTime: profileCache.stale }); }
export function useSessions() { return useQuery<UserSession[]>({ queryKey: profileKeys.sessions(), queryFn: profileRepo.sessions, staleTime: profileCache.sessionStale }); }
export function useRevokeSession() { const qc = useQueryClient(); return useMutation({ mutationFn: profileRepo.revokeSession, onSettled: () => qc.invalidateQueries({ queryKey: profileKeys.sessions() }) }); }
export function useRevokeAllSessions() { const qc = useQueryClient(); return useMutation({ mutationFn: profileRepo.revokeAll, onSettled: () => qc.invalidateQueries({ queryKey: profileKeys.sessions() }) }); }
export function useDeleteAccount() { return useMutation({ mutationFn: profileRepo.deleteAccount }); }
export function useExportData() { return useMutation({ mutationFn: profileRepo.exportData }); }

// ── Navigation ──
const PStack = createNativeStackNavigator();
export function ProfileStack() { return <PStack.Navigator screenOptions={{ headerShown: false }}><PStack.Screen name="Profile" component={ProfileScreen} /></PStack.Navigator>; }

// ── Screen ──
export function ProfileScreen({ navigation }: any) {
  const { palette } = useTheme();
  const { data: profile, isLoading } = useProfile();
  const { data: stats } = useUserStats();
  const { data: sessions } = useSessions();
  const revoke = useRevokeSession();
  const revokeAll = useRevokeAllSessions();
  const del = useDeleteAccount();
  const exportData = useExportData();
  const { theme, developerMode } = useProfileStore();

  return (
    <SafeAreaView style={[ps.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
        <View style={[ps.card, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
          <View style={[ps.avatar, { backgroundColor: palette.surface.elevated }]}><Text style={{ fontSize: 36 }}>👤</Text></View>
          <Text style={[typography.title, { color: palette.text.primary, marginTop: 12 }]}>{profile?.displayName || profile?.username || 'Fighter'}</Text>
          <Text style={[typography.bodySmall, { color: palette.text.secondary }]}>{profile?.email}</Text>
          {profile?.role && <View style={[ps.role, { backgroundColor: palette.primary[500] }]}><Text style={[typography.caption, { color: '#FFF', fontWeight: '700' }]}>{profile.role.toUpperCase()}</Text></View>}
        </View>

        {stats && (
          <View style={[ps.stats, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
            {[{ l: 'Predictions', v: stats.predictions }, { l: 'Favorites', v: stats.favorites }, { l: 'Watchlist', v: stats.watchlist }, { l: 'Days', v: stats.accountAge }].map(({ l, v }) => (
              <View key={l} style={{ alignItems: 'center', minWidth: 70 }}><Text style={[typography.title, { color: palette.text.primary }]}>{v}</Text><Text style={[typography.caption, { color: palette.text.secondary }]}>{l}</Text></View>
            ))}
          </View>
        )}

        <Section title="Appearance" palette={palette}>
          {(['light', 'dark', 'amoled', 'system'] as const).map((t) => (
            <TouchableOpacity key={t} onPress={() => profileActions.setTheme(t)} style={ps.opt}>
              <Text style={[typography.body, { color: palette.text.primary, textTransform: 'capitalize' }]}>{t}</Text>
              {theme === t && <Text style={{ color: palette.primary[400] }}>✓</Text>}
            </TouchableOpacity>
          ))}
        </Section>

        {sessions && sessions.length > 0 && (
          <Section title="Sessions" palette={palette}>
            {sessions.slice(0, 3).map((s: UserSession) => (
              <View key={s.id} style={ps.opt}>
                <View style={{ flex: 1 }}>
                  <Text style={[typography.bodySmall, { color: palette.text.primary }]}>{s.device} {s.current ? '(Now)' : ''}</Text>
                  <Text style={[typography.caption, { color: palette.text.secondary }]}>{s.os} · {s.location}</Text>
                </View>
                <TouchableOpacity onPress={() => revoke.mutate(s.id)}><Text style={[typography.caption, { color: '#EF4444' }]}>Revoke</Text></TouchableOpacity>
              </View>
            ))}
            {sessions.length > 3 && <TouchableOpacity onPress={() => revokeAll.mutate()} style={{ padding: spacing.md }}><Text style={[typography.bodySmall, { color: '#EF4444', textAlign: 'center' }]}>Revoke all sessions</Text></TouchableOpacity>}
          </Section>
        )}

        <Section title="Data" palette={palette}>
          <TouchableOpacity onPress={() => exportData.mutate()} style={ps.opt}><Text style={[typography.body, { color: palette.text.primary }]}>📦 Export data</Text></TouchableOpacity>
          <TouchableOpacity onPress={() => Alert.alert('Delete Account', 'This is permanent.', [{ text: 'Cancel', style: 'cancel' }, { text: 'Delete', style: 'destructive', onPress: () => del.mutate() }])} style={ps.opt}><Text style={[typography.body, { color: '#EF4444' }]}>🗑 Delete account</Text></TouchableOpacity>
        </Section>

        <Section title="Developer" palette={palette}>
          <View style={[ps.opt, { flexDirection: 'row', justifyContent: 'space-between' }]}>
            <Text style={[typography.body, { color: palette.text.primary }]}>Developer mode</Text>
            <Switch value={developerMode} onValueChange={profileActions.toggleDev} />
          </View>
        </Section>

        <Text style={[typography.caption, { color: palette.text.tertiary, textAlign: 'center', marginTop: 40 }]}>MMA Intelligence v1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

function Section({ title, palette, children }: any) {
  return (
    <View style={{ marginTop: spacing.xl }}>
      <Text style={[ps.secTitle, { color: palette.text.tertiary }]}>{title}</Text>
      <View style={[ps.sec, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>{children}</View>
    </View>
  );
}

const ps = StyleSheet.create({
  root: { flex: 1 },
  card: { alignItems: 'center', padding: spacing.xl, borderRadius: radius.lg, borderWidth: 0.5, marginBottom: spacing.xl },
  avatar: { width: 72, height: 72, borderRadius: 36, alignItems: 'center', justifyContent: 'center' },
  role: { marginTop: 8, paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12 },
  stats: { flexDirection: 'row', justifyContent: 'space-around', padding: spacing.lg, borderRadius: radius.lg, borderWidth: 0.5, marginBottom: spacing.xl },
  secTitle: { fontSize: 12, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 },
  sec: { borderRadius: radius.md, borderWidth: 0.5, overflow: 'hidden' },
  opt: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 14, paddingHorizontal: spacing.md, borderBottomWidth: 0.5, borderBottomColor: '#2A2A3E' },
});
