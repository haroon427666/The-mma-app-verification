/** Profile API + store */

import { useQuery } from '@tanstack/react-query';
import { create } from 'zustand';
import api from '@/services/api';

export function useProfile() {
  return useQuery({ queryKey: ['profile'], queryFn: async () => {
    const { data } = await api.get('/v1/me'); return data;
  }, staleTime: 5 * 60 * 1000 });
}

export function useSessions() {
  return useQuery({ queryKey: ['sessions'], queryFn: async () => {
    const { data } = await api.get('/v1/me/sessions'); return data.data ?? [];
  }, staleTime: 60 * 1000 });
}

export const useProfileStore = create<{ activeSection: string | null }>(() => ({ activeSection: null }));
