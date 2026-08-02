/** useCountdown — real-time countdown with background awareness */

import { useState, useEffect, useCallback, useRef } from 'react';
import { AppState } from 'react-native';
import type { CountdownState } from '../types';

export function useCountdown(targetDate: string | null): CountdownState {
  const compute = useCallback((): CountdownState => {
    if (!targetDate) return { days: 0, hours: 0, minutes: 0, seconds: 0, isPast: true, isLive: false, isStartingSoon: false };
    const diff = new Date(targetDate).getTime() - Date.now();
    if (diff <= 0) return { days: 0, hours: 0, minutes: 0, seconds: 0, isPast: true, isLive: false, isStartingSoon: false };
    return {
      days: Math.floor(diff / 86400000),
      hours: Math.floor((diff % 86400000) / 3600000),
      minutes: Math.floor((diff % 3600000) / 60000),
      seconds: Math.floor((diff % 60000) / 1000),
      isPast: false, isLive: false,
      isStartingSoon: diff < 3600000,
    };
  }, [targetDate]);

  const [state, setState] = useState<CountdownState>(compute);
  const intervalRef = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    setState(compute());
    intervalRef.current = setInterval(() => setState(compute()), 1000);

    const sub = AppState.addEventListener('change', (s) => {
      if (s === 'active') setState(compute());
    });

    return () => {
      clearInterval(intervalRef.current);
      sub.remove();
    };
  }, [compute]);

  return state;
}
