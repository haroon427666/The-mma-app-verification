/** Events navigation stack */

import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { EventsScreen } from '../screens/EventsScreen';
import { EventDetailScreen } from '../screens/EventDetailScreen';
import { FightCardScreen } from '../screens/FightCardScreen';
import { LiveEventScreen } from '../screens/LiveEventScreen';
import { ResultsScreen } from '../screens/ResultsScreen';
import { EventStatisticsScreen } from '../screens/ResultsScreen';

export type EventsStackParamList = {
  EventsList: undefined;
  EventDetail: { eventId: string };
  FightCard: { eventId: string; fightId?: string };
  LiveEvent: { eventId: string };
  Results: { eventId: string };
  EventStatistics: { eventId: string };
};

const Stack = createNativeStackNavigator<EventsStackParamList>();

export function EventsStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
      <Stack.Screen name="EventsList" component={EventsScreen} />
      <Stack.Screen name="EventDetail" component={EventDetailScreen} />
      <Stack.Screen name="FightCard" component={FightCardScreen} />
      <Stack.Screen name="LiveEvent" component={LiveEventScreen} />
      <Stack.Screen name="Results" component={ResultsScreen} />
      <Stack.Screen name="EventStatistics" component={EventStatisticsScreen} />
    </Stack.Navigator>
  );
}
