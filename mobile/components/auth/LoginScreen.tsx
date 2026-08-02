/** Login screen — email/password + biometric + remember me */

import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  KeyboardAvoidingView, Platform, ActivityIndicator, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '@/hooks/useAuth';
import { useTheme } from '@/hooks/useTheme';
import { authService } from '@/services/auth';
import { spacing, radius, shadows } from '@/theme';

const loginSchema = z.object({
  email: z.string().email('Valid email required'),
  password: z.string().min(1, 'Password required'),
});

type LoginForm = z.infer<typeof loginSchema>;

export function LoginScreen({ navigation }: any) {
  const [error, setError] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const { login, isLoading } = useAuth();
  const { palette } = useTheme();

  const { control, handleSubmit } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  const onSubmit = async (data: LoginForm) => {
    setError('');
    try {
      await login(data.email, data.password, rememberMe);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.error || 'Login failed');
    }
  };

  const handleBiometric = async () => {
    const available = await authService.isBiometricAvailable();
    if (!available) {
      Alert.alert('Biometric unavailable', 'Set up Face ID or fingerprint in device settings.');
      return;
    }
    const ok = await authService.authenticateWithBiometric();
    if (ok) {
      const restored = await authService.restoreSession();
      if (!restored) setError('Session expired. Please login manually.');
    }
  };

  return (
    <SafeAreaView style={[styles.root, { backgroundColor: palette.surface.bg }]}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.flex}>
        <View style={styles.container}>
          <Text style={[styles.title, { color: palette.text.primary }]}>Welcome back</Text>
          <Text style={[styles.subtitle, { color: palette.text.secondary }]}>Sign in to continue</Text>

          {error ? <Text style={styles.error}>{error}</Text> : null}

          <Controller
            control={control}
            name="email"
            render={({ field, fieldState }) => (
              <View style={styles.field}>
                <Text style={[styles.label, { color: palette.text.secondary }]}>Email</Text>
                <TextInput
                  style={[styles.input, {
                    backgroundColor: palette.surface.card, color: palette.text.primary,
                    borderColor: fieldState.error ? '#EF4444' : palette.surface.border,
                  }]}
                  placeholder="you@example.com"
                  placeholderTextColor={palette.text.tertiary}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoComplete="email"
                  value={field.value}
                  onChangeText={field.onChange}
                />
              </View>
            )}
          />

          <Controller
            control={control}
            name="password"
            render={({ field, fieldState }) => (
              <View style={styles.field}>
                <Text style={[styles.label, { color: palette.text.secondary }]}>Password</Text>
                <TextInput
                  style={[styles.input, {
                    backgroundColor: palette.surface.card, color: palette.text.primary,
                    borderColor: fieldState.error ? '#EF4444' : palette.surface.border,
                  }]}
                  placeholder="Enter password"
                  placeholderTextColor={palette.text.tertiary}
                  secureTextEntry
                  value={field.value}
                  onChangeText={field.onChange}
                />
              </View>
            )}
          />

          <View style={styles.row}>
            <TouchableOpacity onPress={() => setRememberMe(!rememberMe)} style={styles.checkRow}>
              <View style={[styles.checkbox, rememberMe && styles.checkboxChecked]}>
                {rememberMe && <Text style={styles.checkmark}>✓</Text>}
              </View>
              <Text style={[styles.checkLabel, { color: palette.text.secondary }]}>Remember me</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => navigation.navigate('forgotPassword')}>
              <Text style={[styles.link, { color: palette.primary[400] }]}>Forgot?</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={[styles.button, isLoading && styles.buttonDisabled]}
            onPress={handleSubmit(onSubmit)}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#FFF" />
            ) : (
              <Text style={styles.buttonText}>Sign In</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity onPress={handleBiometric} style={styles.biometricBtn}>
            <Text style={[styles.link, { color: palette.primary[400] }]}>🔐 Sign in with biometrics</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={() => navigation.navigate('register')} style={styles.footer}>
            <Text style={{ color: palette.text.secondary }}>
              Don't have an account?{' '}
              <Text style={{ color: palette.primary[400], fontWeight: '600' }}>Sign up</Text>
            </Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  flex: { flex: 1 },
  container: { flex: 1, padding: spacing.xl, justifyContent: 'center' },
  title: { fontSize: 32, fontWeight: '700', marginBottom: 4 },
  subtitle: { fontSize: 16, marginBottom: 32 },
  error: { color: '#EF4444', backgroundColor: '#FEF2F2', padding: 12, borderRadius: radius.sm, marginBottom: 16, fontSize: 14 },
  field: { marginBottom: spacing.lg },
  label: { fontSize: 14, fontWeight: '500', marginBottom: 6 },
  input: { height: 48, borderWidth: 1, borderRadius: radius.md, paddingHorizontal: 14, fontSize: 16 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.xl },
  checkRow: { flexDirection: 'row', alignItems: 'center' },
  checkbox: { width: 20, height: 20, borderWidth: 1.5, borderColor: '#6B7280', borderRadius: 4, marginRight: 8, alignItems: 'center', justifyContent: 'center' },
  checkboxChecked: { backgroundColor: '#3B82F6', borderColor: '#3B82F6' },
  checkmark: { color: '#FFF', fontSize: 12 },
  checkLabel: { fontSize: 14 },
  link: { fontSize: 14, fontWeight: '500' },
  button: { backgroundColor: '#3B82F6', height: 52, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center', ...shadows.md },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#FFF', fontSize: 16, fontWeight: '600' },
  biometricBtn: { alignItems: 'center', marginTop: spacing.lg, padding: spacing.md },
  footer: { alignItems: 'center', marginTop: spacing.xxxl },
});
