import { Animated } from 'react-native';
import { durations, easings } from '../tokens';

export function fadeIn(anim: Animated.Value, toValue = 1, duration = durations.normal) { return Animated.timing(anim, { toValue, duration, useNativeDriver: true }); }
export function fadeOut(anim: Animated.Value, duration = durations.fast) { return Animated.timing(anim, { toValue: 0, duration, useNativeDriver: true }); }
export function scaleIn(anim: Animated.Value, toValue = 1) { return Animated.spring(anim, { toValue, ...easings.spring, useNativeDriver: true }); }
export function scaleOut(anim: Animated.Value) { return Animated.timing(anim, { toValue: 0, duration: durations.fast, useNativeDriver: true }); }
export function slideUp(anim: Animated.Value, from = 50, to = 0) { anim.setValue(from); return Animated.spring(anim, { toValue: to, ...easings.spring, useNativeDriver: true }); }
export function slideDown(anim: Animated.Value, to = 100, duration = durations.fast) { return Animated.timing(anim, { toValue: to, duration, useNativeDriver: true }); }
export function livePulse(anim: Animated.Value) { return Animated.loop(Animated.sequence([Animated.timing(anim, { toValue: 1, duration: 600, useNativeDriver: true }), Animated.timing(anim, { toValue: 0.2, duration: 600, useNativeDriver: true })])); }
export function countdownFlip(anim: Animated.Value) { return Animated.spring(anim, { toValue: 1, ...easings.spring, useNativeDriver: true }); }
export function spring(config = easings.spring) { return config; }