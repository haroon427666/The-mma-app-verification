/** Container + Grid + Stack — layout primitives */
import React from 'react';
import { View, StyleSheet } from 'react-native';
import { useTheme } from '../../theme';
import { spacing } from '../../tokens';

export const Container = ({ children, maxWidth = 1200 }: { children: React.ReactNode; maxWidth?: number }) => (
  <View style={{ width: '100%', maxWidth, alignSelf: 'center', paddingHorizontal: spacing.lg }}>{children}</View>
);

export const Grid = ({ children, cols = 2, gap = spacing.md }: { children: React.ReactNode; cols?: number; gap?: number }) => (
  <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap }}>{React.Children.map(children, child => <View style={{ width: `${100 / cols}%`, paddingHorizontal: gap / 2 }}>{child}</View>)}</View>
);

export const Stack = ({ children, gap = spacing.sm, direction = 'column', align = 'start' }: { children: React.ReactNode; gap?: number; direction?: 'row' | 'column'; align?: 'start' | 'center' | 'end' | 'stretch' }) => {
  const alignItems = align === 'start' ? 'flex-start' : align === 'end' ? 'flex-end' : align === 'center' ? 'center' : 'stretch';
  return <View style={{ flexDirection: direction, gap, alignItems }}>{children}</View>;
};

export const Spacer = ({ size = spacing.md, axis = 'vertical' }: { size?: number; axis?: 'vertical' | 'horizontal' }) => (
  <View style={{ [axis === 'vertical' ? 'height' : 'width']: size }} />
);