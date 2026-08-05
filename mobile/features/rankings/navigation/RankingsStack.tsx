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
      <Stack.Screen name="PoundForPound" getComponent={() => require('../screens').PoundForPoundScreen} />
      <Stack.Screen name="DivisionRankings" getComponent={() => require('../screens').DivisionRankingsScreen} />
      <Stack.Screen name="RankingHistory" getComponent={() => require('../screens').RankingHistoryScreen} />
      <Stack.Screen name="RankMovement" getComponent={() => require('../screens').RankMovementScreen} />
      <Stack.Screen name="ChampionHistory" getComponent={() => require('../screens').ChampionHistoryScreen} />
      <Stack.Screen name="TitleDefenses" getComponent={() => require('../screens').TitleDefensesScreen} />
      <Stack.Screen name="GOATRankings" getComponent={() => require('../screens').GOATRankingsScreen} />
      <Stack.Screen name="Prospects" getComponent={() => require('../screens').ProspectsScreen} />
      <Stack.Screen name="CompareRankings" getComponent={() => require('../screens').CompareRankingsScreen} />
    </Stack.Navigator>
  );
}
