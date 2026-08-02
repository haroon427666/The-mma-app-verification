/** UI store — theme, navigation, loading states */

import { create } from 'zustand';
import type { ThemeMode } from '@/types';

interface UIState {
  theme: ThemeMode;
  isSplashVisible: boolean;
  isMaintenanceMode: boolean;
  activeModal: string | null;
  toastMessage: string | null;

  setTheme: (theme: ThemeMode) => void;
  hideSplash: () => void;
  setMaintenance: (on: boolean) => void;
  showModal: (name: string) => void;
  hideModal: () => void;
  showToast: (message: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  theme: 'system',
  isSplashVisible: true,
  isMaintenanceMode: false,
  activeModal: null,
  toastMessage: null,

  setTheme: (theme) => set({ theme }),
  hideSplash: () => set({ isSplashVisible: false }),
  setMaintenance: (on) => set({ isMaintenanceMode: on }),
  showModal: (name) => set({ activeModal: name }),
  hideModal: () => set({ activeModal: null }),
  showToast: (msg) => {
    set({ toastMessage: msg });
    setTimeout(() => set({ toastMessage: null }), 3000);
  },
}));
