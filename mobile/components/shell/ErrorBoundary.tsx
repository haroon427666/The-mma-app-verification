/** Error Boundary — catches render errors with fallback UI */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

interface Props { children: React.ReactNode; }
interface State { hasError: boolean; error: Error | null; }

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  handleRetry = () => this.setState({ hasError: false, error: null });

  render() {
    if (this.state.hasError) {
      return (
        <View style={styles.container}>
          <Text style={styles.icon}>⚠️</Text>
          <Text style={styles.title}>Something went wrong</Text>
          <Text style={styles.message}>{this.state.error?.message || 'An unexpected error occurred'}</Text>
          <TouchableOpacity style={styles.button} onPress={this.handleRetry}>
            <Text style={styles.buttonText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      );
    }
    return this.props.children;
  }
}

export function OfflineFallback({ onRetry }: { onRetry: () => void }) {
  return (
    <View style={styles.container}>
      <Text style={styles.icon}>📡</Text>
      <Text style={styles.title}>No connection</Text>
      <Text style={styles.message}>Check your internet and try again</Text>
      <TouchableOpacity style={styles.button} onPress={onRetry}>
        <Text style={styles.buttonText}>Retry</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0A0A0A', padding: 32 },
  icon: { fontSize: 56, marginBottom: 16 },
  title: { color: '#F9FAFB', fontSize: 22, fontWeight: '700', marginBottom: 8 },
  message: { color: '#9CA3AF', fontSize: 14, textAlign: 'center', marginBottom: 24 },
  button: { backgroundColor: '#3B82F6', paddingVertical: 14, paddingHorizontal: 32, borderRadius: 12 },
  buttonText: { color: '#FFF', fontSize: 16, fontWeight: '600' },
});
