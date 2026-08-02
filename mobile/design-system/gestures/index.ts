import { PanResponder, GestureResponderEvent, PanResponderGestureState } from 'react-native';

export function createSwipeGesture(onSwipeLeft?: () => void, onSwipeRight?: () => void) {
  return PanResponder.create({
    onMoveShouldSetPanResponder: (_, g) => Math.abs(g.dx) > 20 && Math.abs(g.dy) < 20,
    onPanResponderRelease: (_, g) => { if (g.dx < -80) onSwipeLeft?.(); else if (g.dx > 80) onSwipeRight?.(); },
  });
}

export function createDragGesture(onDragEnd?: (x: number, y: number) => void) {
  return PanResponder.create({
    onStartShouldSetPanResponder: () => true,
    onPanResponderRelease: (_e, g) => onDragEnd?.(g.dx, g.dy),
  });
}

export function createPinchGesture(onScale?: (s: number) => void) {
  return PanResponder.create({
    onStartShouldSetPanResponder: () => true,
    onPanResponderMove: (_e: GestureResponderEvent, g: PanResponderGestureState) => {
      const scale = Math.sqrt(g.dx * g.dx + g.dy * g.dy) / 100 + 1;
      onScale?.(Math.max(0.5, Math.min(3, scale)));
    },
  });
}

export function createLongPressGesture(onLongPress: () => void, delay = 500) {
  return {
    onLongPress,
    delayLongPress: delay,
  };
}