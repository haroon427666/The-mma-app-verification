/** EventCard story */
import React from 'react';
import { View } from 'react-native';
import { EventCard } from '../components/EventCard';

const palette = { surface: { card: '#1A1A2E', bg: '#0A0A0A', border: '#2A2A3E', elevated: '#222240' }, text: { primary: '#FFF', secondary: '#9CA3AF', tertiary: '#6B7280' } };

const mockEvent = {
  id: '1', name: 'UFC 400: Makhachev vs Topuria', date: '2025-03-15T22:00:00Z',
  venue: 'Madison Square Garden', city: 'New York', country: 'USA',
  fightCount: 13, broadcasters: ['ESPN+ PPV'], status: 'SCHEDULED', isLive: false,
} as any;

export default {
  title: 'Events/EventCard',
  component: EventCard,
};

export const Upcoming = () => <View style={{ padding: 20, backgroundColor: '#0A0A0A' }}><EventCard event={mockEvent} palette={palette} onPress={() => {}} /></View>;
export const Live = () => <View style={{ padding: 20, backgroundColor: '#0A0A0A' }}><EventCard event={{ ...mockEvent, isLive: true, status: 'LIVE' }} palette={palette} onPress={() => {}} /></View>;
