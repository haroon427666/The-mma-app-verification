/** Main navigator — 9 tabs wiring all production feature stacks */

import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { View, Text, StyleSheet } from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import { HomeScreen } from '@/features/home';
import { EventsStack } from '@/features/events';
import { FightersStack } from '@/features/fighters';
import { RankingsStack } from '@/features/rankings';
import { PredictionsStack } from '@/features/predictions';
import { RecommendationsStack } from '@/features/recommendations/RecsModule';
import { SearchStack } from '@/features/search/SearchModule';
import { WatchlistStack } from '@/features/watchlist/WatchModule';
import { NotificationsStack } from '@/features/notifications/NotifsModule';
import { ProfileStack } from '@/features/profile/ProfileModule';

const Tab = createBottomTabNavigator();

function TabIcon({ name, focused }: { name: string; focused: boolean }) {
  const icons: Record<string, string> = {
    home: '🥊', events: '📅', fighters: '👤',
    rankings: '🏆', predictions: '🔮', search: '🔍',
    watchlist: '👁', notifications: '🔔', profile: '⚙',
  };
  return (
    <View style={s.iconWrap}>
      <Text style={[s.icon, focused && s.iconFocused]}>{icons[name] || '●'}</Text>
    </View>
  );
}

export function MainNavigator() {
  const { palette } = useTheme();

  return (
    <Tab.Navigator screenOptions={({ route }) => ({
      headerShown: false,
      tabBarIcon: ({ focused }) => <TabIcon name={route.name} focused={focused} />,
      tabBarActiveTintColor: palette.primary[400],
      tabBarInactiveTintColor: palette.text.secondary,
      tabBarStyle: {
        backgroundColor: palette.surface.card,
        borderTopColor: palette.surface.border,
        borderTopWidth: 0.5, paddingBottom: 4, height: 56,
      },
      tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
    })}>
      <Tab.Screen name="home" component={HomeScreen} options={{ tabBarLabel: 'Home' }} />
      <Tab.Screen name="events" component={EventsStack} options={{ tabBarLabel: 'Events' }} />
      <Tab.Screen name="fighters" component={FightersStack} options={{ tabBarLabel: 'Fighters' }} />
      <Tab.Screen name="rankings" component={RankingsStack} options={{ tabBarLabel: 'Rank' }} />
      <Tab.Screen name="predictions" component={PredictionsStack} options={{ tabBarLabel: 'Predict' }} />
      <Tab.Screen name="search" component={SearchStack} options={{ tabBarLabel: 'Search' }} />
      <Tab.Screen name="watchlist" component={WatchlistStack} options={{ tabBarLabel: 'Track' }} />
      <Tab.Screen name="notifications" component={NotificationsStack} options={{ tabBarLabel: 'Alerts' }} />
      <Tab.Screen name="profile" component={ProfileStack} options={{ tabBarLabel: 'You' }} />
    </Tab.Navigator>
  );
}

const s = StyleSheet.create({
  iconWrap: { alignItems: 'center', justifyContent: 'center' },
  icon: { fontSize: 20, opacity: 0.4 },
  iconFocused: { opacity: 1, transform: [{ scale: 1.15 }] },
});
