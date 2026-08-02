import React, { useEffect, useRef } from 'react';
import { Animated, Text, StyleSheet } from 'react-native';
export interface ToastProps { visible: boolean; message: string; type?: 'info' | 'success' | 'error' | 'warning'; onDismiss: () => void; }
export const Toast = ({ visible, message, type = 'info', onDismiss }: ToastProps) => {
  const colors = { info: '#3B82F6', success: '#10B981', error: '#EF4444', warning: '#F59E0B' };
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => { Animated.timing(anim, { toValue: visible ? 1 : 0, duration: 300, useNativeDriver: true }).start(); if (visible) { const t = setTimeout(onDismiss, 3000); return () => clearTimeout(t); } }, [visible]);
  if (!visible) return null;
  return (<Animated.View style={[s.wrap, { backgroundColor: colors[type], opacity: anim, transform: [{ translateY: anim.interpolate({ inputRange: [0, 1], outputRange: [-60, 0] }) }] }]}><Text style={s.text}>{message}</Text></Animated.View>);
};
const s = StyleSheet.create({ wrap: { position: 'absolute', top: 60, left: 16, right: 16, paddingVertical: 14, paddingHorizontal: 20, borderRadius: 12, zIndex: 9999, alignItems: 'center', elevation: 10 }, text: { color: '#FFF', fontSize: 14, fontWeight: '600' } });