/** Profile module — user info, sessions, theme, account actions */

import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';
import { useTheme } from '@/hooks/useTheme';
import { useAuthStore } from '@/stores/auth';
import { useUIStore } from '@/stores/ui';
import { authService } from '@/services/auth';
import { typography, spacing, radius } from '@/theme';
import type { ThemeMode } from '@/types';

// ── Types ──
export interface UserProfile { id: string; email: string; username: string; displayName: string | null; avatarUrl: string | null; role: string; emailVerified: boolean; createdAt: string; preferences: any; }
export interface SessionInfo { id: string; device: string; browser: string; os: string; ip: string; country: string; lastSeen: string; isCurrent: boolean; }

// ── API + Repository ──
export const profileApi = { me: () => api.get('/v1/me'), sessions: () => api.get('/v1/me/sessions'), updatePreferences: (p: any) => api.patch('/v1/me/preferences', p), deleteAccount: () => api.delete('/v1/me') };
export const profileRepo = {
  me: async () => { const { data } = await profileApi.me(); return data as UserProfile; },
  sessions: async () => { const { data } = await profileApi.sessions(); return (data?.data ?? data) as SessionInfo[]; },
  updatePreferences: async (p: any) => { await profileApi.updatePreferences(p); },
  deleteAccount: async () => { await profileApi.deleteAccount(); },
};

// ── Services ──
export const profileKeys = { me: () => ['profile', 'me'] as const, sessions: () => ['profile', 'sessions'] as const };

// ── Store ──
export const useProfileStore = create<{ activeSection: string | null }>(() => ({ activeSection: null }));

// ── Hooks ──
export function useProfile() { return useQuery<UserProfile>({ queryKey: profileKeys.me(), queryFn: profileRepo.me, staleTime: 5 * 60_1000 }); }
export function useSessions() { return useQuery<SessionInfo[]>({ queryKey: profileKeys.sessions(), queryFn: profileRepo.sessions, staleTime: 60_1000 }); }

// ── Screen ──
export function ProfileScreen() {
  const { palette } = useTheme();
  const user = useAuthStore((s) => s.user) as UserProfile | null;
  const theme = useUIStore((s) => s.theme);
  const setTheme = useUIStore((s) => s.setTheme);

  const handleDelete = () => Alert.alert('Delete Account', 'This is permanent and cannot be undone.', [{ text: 'Cancel', style: 'cancel' }, { text: 'Delete', style: 'destructive', onPress: () => authService.deleteAccount() }]);

  return (
    <SafeAreaView style={[st.root, { backgroundColor: palette.surface.bg }]}>
      <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
        <View style={[st.profHead, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>
          <View style={[st.avatar, { backgroundColor: palette.surface.elevated }]}><Text style={{ fontSize: 32 }}>👤</Text></View>
          <Text style={[typography.title, { color: palette.text.primary, marginTop: 12 }]}>{user?.displayName || user?.username || 'Fighter'}</Text>
          <Text style={[typography.bodySmall, { color: palette.text.secondary }]}>{user?.email}</Text>
          <View style={[st.role, { backgroundColor: palette.primary[500] }]}><Text style={[typography.caption, { color: '#FFF', fontWeight: '700' }]}>{user?.role?.toUpperCase()}</Text></View>
        </View>

        <Section title="Appearance" palette={palette}>
          {(['light', 'dark', 'amoled', 'system'] as ThemeMode[]).map((t) => (
            <TouchableOpacity key={t} onPress={() => setTheme(t)} style={st.opt}>
              <Text style={[typography.body, { color: palette.text.primary }]}>{t.charAt(0).toUpperCase() + t.slice(1)}</Text>
              {theme === t && <Text style={{ color: palette.primary[400], fontWeight: '700' }}>✓</Text>}
            </TouchableOpacity>
          ))}
        </Section>

        <Section title="Account" palette={palette}>
          <TouchableOpacity onPress={() => authService.logout()} style={st.opt}><Text style={[typography.body, { color: palette.text.primary }]}>Log out</Text></TouchableOpacity>
          <TouchableOpacity onPress={() => authService.logoutAll()} style={st.opt}><Text style={[typography.body, { color: palette.text.primary }]}>Log out all devices</Text></TouchableOpacity>
          <TouchableOpacity onPress={handleDelete} style={st.opt}><Text style={[typography.body, { color: '#EF4444' }]}>Delete account</Text></TouchableOpacity>
        </Section>

        {user?.createdAt && <Text style={[typography.caption, { color: palette.text.tertiary, textAlign: 'center', marginTop: 20 }]}>Member since {new Date(user.createdAt).toLocaleDateString()}</Text>}
        <Text style={[typography.caption, { color: palette.text.tertiary, textAlign: 'center', marginTop: 4 }]}>MMA Intelligence v1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

function Section({ title, palette, children }: any) {
  return (
    <View style={{ marginTop: spacing.xl }}>
      <Text style={[typography.bodySmall, { color: palette.text.tertiary, textTransform: 'uppercase', fontWeight: '700', marginBottom: 8, letterSpacing: 1 }]}>{title}</Text>
      <View style={[st.section, { backgroundColor: palette.surface.card, borderColor: palette.surface.border }]}>{children}</View>
    </View>
  );
}

const st = StyleSheet.create({
  root: { flex: 1 },
  profHead: { alignItems: 'center', padding: spacing.xl, borderRadius: radius.lg, borderWidth: 0.5 },
  avatar: { width: 72, height: 72, borderRadius: 36, alignItems: 'center', justifyContent: 'center' },
  role: { marginTop: 8, paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12 },
  section: { borderRadius: radius.md, borderWidth: 0.5, overflow: 'hidden' },
  opt: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 14, paddingHorizontal: spacing.md, borderBottomWidth: 0.5, borderBottomColor: '#2A2A3E' },
});
