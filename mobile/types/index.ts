/** Global type definitions */

export type ThemeMode = 'light' | 'dark' | 'amoled' | 'system';
export type AuthStatus = 'idle' | 'loading' | 'authenticated' | 'unauthenticated';
export type NetworkStatus = 'online' | 'offline' | 'flaky';

export interface User {
  id: string;
  email: string;
  username: string;
  displayName: string | null;
  avatarUrl: string | null;
  role: 'user' | 'moderator' | 'admin';
  emailVerified: boolean;
  preferences: UserPreferences;
}

export interface UserPreferences {
  theme: ThemeMode;
  timezone: string;
  defaultHomepage: string;
  defaultSort: string;
  defaultWeightClasses: string[];
  notifyUpcomingFight: boolean;
  notifyEventStarting: boolean;
  notifyRankingChanged: boolean;
  notifyFightCancelled: boolean;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  tokenType: string;
}

export interface ApiError {
  error: string;
  code: number;
  details?: Array<{ message: string }>;
  errorId?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export interface OfflineAction {
  id: string;
  type: string;
  payload: unknown;
  createdAt: string;
  retryCount: number;
}

export interface PushNotificationData {
  type: string;
  title: string;
  message: string;
  payload?: Record<string, unknown>;
}

/** Navigation types */
export type RootStackParamList = {
  auth: undefined;
  main: undefined;
  modal: { screen: string; params?: Record<string, unknown> };
};

export type AuthStackParamList = {
  login: undefined;
  register: undefined;
  forgotPassword: undefined;
  resetPassword: { token: string };
  verifyEmail: { token: string };
};

export type MainTabParamList = {
  home: undefined;
  events: undefined;
  rankings: undefined;
  predictions: undefined;
  profile: undefined;
};
