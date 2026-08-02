/** Settings store */
import { create } from 'zustand';

interface SettingsState {
  language: string; offlineMode: boolean; developerMode: boolean;
  analyticsEnabled: boolean; crashReportingEnabled: boolean;
  notificationsEnabled: boolean; hapticsEnabled: boolean;
}

export const useSettingsStore = create<SettingsState>(() => ({
  language: 'en', offlineMode: false, developerMode: false,
  analyticsEnabled: true, crashReportingEnabled: true,
  notificationsEnabled: true, hapticsEnabled: true,
}));

export const settingsActions = {
  setLanguage: (l: string) => useSettingsStore.setState({ language: l }),
  toggleOffline: () => useSettingsStore.setState((s) => ({ offlineMode: !s.offlineMode })),
  toggleDeveloper: () => useSettingsStore.setState((s) => ({ developerMode: !s.developerMode })),
  toggleAnalytics: () => useSettingsStore.setState((s) => ({ analyticsEnabled: !s.analyticsEnabled })),
  toggleNotifications: () => useSettingsStore.setState((s) => ({ notificationsEnabled: !s.notificationsEnabled })),
};
