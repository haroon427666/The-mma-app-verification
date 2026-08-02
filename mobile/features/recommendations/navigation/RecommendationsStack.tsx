/** Recommendations Navigation */

import { createNativeStackNavigator } from '@react-navigation/native-stack';

export type RecommendationsStackParamList = {
  RecommendationsList: undefined;
  RecommendationDetail: { entityId: string; type: 'fighter' | 'event' | 'fight' };
};

const Stack = createNativeStackNavigator<RecommendationsStackParamList>();

export function RecommendationsStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
      <Stack.Screen name="RecommendationsList" getComponent={() => require('../screens').RecommendationsScreen} />
    </Stack.Navigator>
  );
}
