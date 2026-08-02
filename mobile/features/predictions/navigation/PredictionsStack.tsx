/** Predictions Navigation */

import { createNativeStackNavigator } from '@react-navigation/native-stack';

export type PredictionsStackParamList = {
  PredictionsDashboard: undefined;
  FightPrediction: { fightId: string };
  PredictionReport: { fightId: string };
  MonteCarlo: { fightId: string };
  PredictionHistory: undefined;
  SavedPredictions: undefined;
  ComparePredictions: { fightIdA: string; fightIdB?: string };
};

const Stack = createNativeStackNavigator<PredictionsStackParamList>();

export function PredictionsStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
      <Stack.Screen name="PredictionsDashboard" getComponent={() => require('../screens/PredictionsScreen').PredictionsDashboardScreen} />
      <Stack.Screen name="FightPrediction" getComponent={() => require('../screens/PredictionsScreen').FightPredictionScreen} />
      <Stack.Screen name="PredictionReport" getComponent={() => require('../screens/PredictionsScreen').PredictionReportScreen} />
      <Stack.Screen name="MonteCarlo" getComponent={() => require('../screens/PredictionsScreen').MonteCarloScreen} />
      <Stack.Screen name="PredictionHistory" getComponent={() => require('../screens/PredictionsScreen').PredictionHistoryScreen} />
      <Stack.Screen name="SavedPredictions" getComponent={() => require('../screens/PredictionsScreen').SavedPredictionsScreen} />
      <Stack.Screen name="ComparePredictions" getComponent={() => require('../screens/PredictionsScreen').ComparePredictionsScreen} />
    </Stack.Navigator>
  );
}
