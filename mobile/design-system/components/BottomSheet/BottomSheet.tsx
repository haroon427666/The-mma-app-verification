import React, { useEffect, useRef } from 'react';
import { View, Text, Modal, Pressable, Animated, StyleSheet } from 'react-native';
import { useTheme } from '../../theme'; import { radius } from '../../tokens';
export interface BottomSheetProps { visible: boolean; onDismiss: () => void; title?: string; children: React.ReactNode; }
export const BottomSheet = ({ visible, onDismiss, title, children }: BottomSheetProps) => {
  const { palette } = useTheme();
  const y = useRef(new Animated.Value(500)).current;
  useEffect(() => { Animated.spring(y, { toValue: visible ? 0 : 500, damping: 20, stiffness: 200, useNativeDriver: true }).start(); }, [visible]);
  if (!visible) return null;
  return (<Modal transparent visible={visible} onRequestClose={onDismiss} animationType="none"><Pressable style={s.overlay} onPress={onDismiss} /><Animated.View style={[s.sheet, { backgroundColor: palette.surface.card, transform: [{ translateY: y }] }]}><View style={s.handle} />{title && <Text style={[s.title, { color: palette.text.primary }]}>{title}</Text>}{children}</Animated.View></Modal>);
};
const s = StyleSheet.create({ overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)' }, sheet: { position: 'absolute', bottom: 0, left: 0, right: 0, borderTopLeftRadius: radius.xl, borderTopRightRadius: radius.xl, padding: 24, paddingBottom: 40 }, handle: { width: 36, height: 4, borderRadius: 2, backgroundColor: '#4B5563', alignSelf: 'center', marginBottom: 24 }, title: { fontSize: 18, fontWeight: '700', marginBottom: 24, textAlign: 'center' } });