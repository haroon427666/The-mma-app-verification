/** Animation files — shake, shimmer, hero, transition, navigation */

import { Animated } from 'react-native';
import { easings, durations } from '../tokens';

// ── Shake ──
export function shake(anim: Animated.Value, intensity = 10) {
  return Animated.sequence([
    Animated.timing(anim, { toValue: intensity, duration: 50, useNativeDriver: true }),
    Animated.timing(anim, { toValue: -intensity, duration: 50, useNativeDriver: true }),
    Animated.timing(anim, { toValue: intensity / 2, duration: 50, useNativeDriver: true }),
    Animated.timing(anim, { toValue: 0, duration: 50, useNativeDriver: true }),
  ]);
}

// ── Shimmer ──
export function shimmer(anim: Animated.Value) {
  return Animated.loop(
    Animated.sequence([
      Animated.timing(anim, { toValue: 1, duration: 1000, useNativeDriver: true }),
      Animated.timing(anim, { toValue: 0, duration: 1000, useNativeDriver: true }),
    ])
  );
}

// ── Hero / Shared Element ──
export function heroTransition(tag: string) { return { sharedTransitionTag: tag }; }

// ── Navigation Transitions ──
export const navigationTransitions = {
  slideFromRight: { animation: 'slide_from_right' as const },
  fade: { animation: 'fade' as const },
  none: { animation: 'none' as const },
};

// ── Card Expansion ──
export function cardExpand(scaleAnim: Animated.Value, heightAnim: Animated.Value, expanded: boolean) {
  const toScale = expanded ? 1 : 0.95;
  const toHeight = expanded ? 1 : 0;
  return Animated.parallel([
    Animated.spring(scaleAnim, { toValue: toScale, ...easings.spring, useNativeDriver: true }),
    Animated.timing(heightAnim, { toValue: toHeight, duration: durations.normal, useNativeDriver: false }),
  ]);
}

// ── Page Transitions ──
export function pageTransition(anim: Animated.Value, direction: 'forward' | 'backward') {
  const from = direction === 'forward' ? 30 : -30;
  const to = 0;
  anim.setValue(from);
  return Animated.timing(anim, { toValue: to, duration: durations.normal, useNativeDriver: true });
}