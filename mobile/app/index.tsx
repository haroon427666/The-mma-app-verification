import React from 'react';
import { useRouter } from 'expo-router';
import { HomeScreen } from '@/features/home';

export default function HomeRoute() {
  const router = useRouter();

  const navigation = {
    navigate: (screen: string, opts?: { screen?: string; params?: { id?: string } }) => {
      if (screen === 'events') {
        const id = opts?.params?.id;
        router.push(id ? `/events?id=${id}` : '/events');
        return;
      }
      if (screen === 'fighters') router.push('/fighters');
      if (screen === 'rankings') router.push('/rankings');
    },
  };

  return <HomeScreen navigation={navigation} />;
}