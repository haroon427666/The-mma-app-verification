/** Fighters Navigation */

import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { FightersScreen, FighterProfileScreen, FighterStatsScreen, SimilarFightersScreen, FighterComparisonScreen, AchievementsScreen, MediaScreen } from '../screens';

export type FightersStackParamList = {
  FightersList: undefined;
  FighterProfile: { fighterId: string };
  FighterStats: { fighterId: string };
  FighterComparison: { fighterA: string; fighterB?: string };
  SimilarFighters: { fighterId: string };
  Achievements: { fighterId: string };
  Media: { fighterId: string };
};

const Stack = createNativeStackNavigator<FightersStackParamList>();

export function FightersStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
      <Stack.Screen name="FightersList" component={FightersScreen} />
      <Stack.Screen name="FighterProfile" component={FighterProfileScreen} />
      <Stack.Screen name="FighterStats" component={FighterStatsScreen} />
      <Stack.Screen name="FighterComparison" component={FighterComparisonScreen} />
      <Stack.Screen name="SimilarFighters" component={SimilarFightersScreen} />
      <Stack.Screen name="Achievements" component={AchievementsScreen} />
      <Stack.Screen name="Media" component={MediaScreen} />
    </Stack.Navigator>
  );
}
