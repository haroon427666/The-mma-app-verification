/** Rankings Navigation Stack — 10 screens */

import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

export type RankingsStackParamList = {
  RankingsList: undefined;
  PoundForPound: undefined;
  DivisionRankings: { division: string };
  RankingHistory: { fighterId: string; fighterName: string };
  RankMovement: undefined;
  ChampionHistory: { weightClass?: string };
  TitleDefenses: undefined;
  GOATRankings: undefined;
  Prospects: { division?: string };
  CompareRankings: undefined;
};

const Stack = createNativeStackNavigator<RankingsStackParamList>();

export function RankingsStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
      <Stack.Screen name="RankingsList" getComponent={() => require('../screens').RankingsScreen} />
      <Stack.Screen name="PoundForPound" getComponent={() => Promise.resolve({ default: () => null })} />
      <Stack.Screen name="DivisionRankings" getComponent={() => Promise.resolve({ default: () => null })} />
      <Stack.Screen name="RankingHistory" getComponent={() => Promise.resolve({ default: () => null })} />
      <Stack.Screen name="RankMovement" getComponent={() => Promise.resolve({ default: () => null })} />
      <Stack.Screen name="ChampionHistory" getComponent={() => Promise.resolve({ default: () => null })} />
      <Stack.Screen name="TitleDefenses" getComponent={() => Promise.resolve({ default: () => null })} />
      <Stack.Screen name="GOATRankings" getComponent={() => Promise.resolve({ default: () => null })} />
      <Stack.Screen name="Prospects" getComponent={() => Promise.resolve({ default: () => null })} />
      <Stack.Screen name="CompareRankings" getComponent={() => Promise.resolve({ default: () => null })} />
    </Stack.Navigator>
  );
}
