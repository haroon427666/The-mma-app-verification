/** Error Boundary — catches render errors in provider tree */
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

interface EBProps { children: React.ReactNode; fallback?: React.ReactNode; }
interface EBState { hasError: boolean; error: Error | null; }
export class ErrorBoundary extends React.Component<EBProps, EBState> {
  state: EBState = { hasError: false, error: null };
  static getDerivedStateFromError(e: Error): EBState { return { hasError: true, error: e }; }
  componentDidCatch(e: Error, info: React.ErrorInfo) { console.error('[ErrorBoundary]', e, info); }
  handleRetry = () => this.setState({ hasError: false, error: null });
  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <View style={s.ctr}>
          <Text style={s.icon}>⚠️</Text>
          <Text style={s.title}>Something went wrong</Text>
          <Text style={s.msg}>{this.state.error?.message}</Text>
          <TouchableOpacity onPress={this.handleRetry} style={s.btn}><Text style={s.btnText}>Restart</Text></TouchableOpacity>
        </View>
      );
    }
    return this.props.children;
  }
}
const s = StyleSheet.create({ ctr: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0A0A0A', padding: 40 }, icon: { fontSize: 48 }, title: { color: '#FFF', fontSize: 20, fontWeight: '700', marginTop: 16 }, msg: { color: '#9CA3AF', fontSize: 14, marginTop: 8, textAlign: 'center' }, btn: { marginTop: 24, backgroundColor: '#3B82F6', paddingVertical: 14, paddingHorizontal: 32, borderRadius: 12 }, btnText: { color: '#FFF', fontWeight: '600', fontSize: 16 } });
