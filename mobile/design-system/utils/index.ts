import { StyleSheet } from 'react-native';
import { spacing, radius, elevation, typography } from '../tokens';

export function createShadow(level: keyof typeof elevation) { return elevation[level]; }
export function createSpacing(value: keyof typeof spacing) { return spacing[value]; }
export function createRadius(value: keyof typeof radius) { return radius[value]; }
export function createTextStyle(name: keyof typeof typography) { return typography[name]; }

export const layerStyles = StyleSheet.create({
  card: { padding: spacing.md, borderRadius: radius.lg, backgroundColor: 'inherit', borderWidth: 0, }
});

export function conditionalStyle(condition: boolean, style: any) { return condition ? style : {}; }