/** Animation presets */

export const motion = {
  duration: {
    fast: 150,
    normal: 250,
    slow: 400,
    spring: 500,
  },
  spring: {
    gentle: { damping: 15, stiffness: 120, mass: 1 },
    snappy: { damping: 20, stiffness: 300, mass: 0.8 },
    bouncy: { damping: 8, stiffness: 150, mass: 1 },
  },
  fadeIn: {
    from: { opacity: 0 },
    to: { opacity: 1 },
  },
  slideUp: {
    from: { opacity: 0, transform: [{ translateY: 20 }] },
    to: { opacity: 1, transform: [{ translateY: 0 }] },
  },
  scaleIn: {
    from: { opacity: 0, transform: [{ scale: 0.9 }] },
    to: { opacity: 1, transform: [{ scale: 1 }] },
  },
  skeleton: {
    shimmer: ['#1A1A2E', '#222240', '#1A1A2E'] as const,
    speed: 1200,
  },
} as const;
