/** Register screen */

import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  KeyboardAvoidingView, Platform, ActivityIndicator, ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '@/hooks/useAuth';
import { useTheme } from '@/hooks/useTheme';
import { spacing, radius } from '@/theme';

const registerSchema = z.object({
  email: z.string().email('Valid email required'),
  username: z.string().min(3, 'Min 3 characters').max(50).regex(/^[a-zA-Z0-9_-]+$/, 'Letters, numbers, _, - only'),
  displayName: z.string().max(100).optional(),
  password: z.string().min(8, 'Min 8 characters')
    .regex(/[A-Z]/, 'Need uppercase')
    .regex(/[a-z]/, 'Need lowercase')
    .regex(/[0-9]/, 'Need a digit'),
});

type RegisterForm = z.infer<typeof registerSchema>;

export function RegisterScreen({ navigation }: any) {
  const [error, setError] = useState('');
  const { register, isLoading } = useAuth();
  const { palette } = useTheme();

  const { control, handleSubmit } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: '', username: '', displayName: '', password: '' },
  });

  const onSubmit = async (data: RegisterForm) => {
    setError('');
    try {
      await register(data.email, data.username, data.password, data.displayName);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.error || 'Registration failed');
    }
  };

  return (
    <SafeAreaView style={[styles.root, { backgroundColor: palette.surface.bg }]}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.flex}>
        <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
          <Text style={[styles.title, { color: palette.text.primary }]}>Create account</Text>
          <Text style={[styles.subtitle, { color: palette.text.secondary }]}>Join MMA Intelligence</Text>

          {error ? <Text style={styles.error}>{error}</Text> : null}

          {(['email', 'username', 'displayName', 'password'] as const).map((field) => (
            <Controller
              key={field}
              control={control}
              name={field}
              render={({ field: f, fieldState }) => (
                <View style={styles.field}>
                  <Text style={[styles.label, { color: palette.text.secondary }]}>
                    {field === 'displayName' ? 'Display Name (optional)' : field.charAt(0).toUpperCase() + field.slice(1)}
                  </Text>
                  <TextInput
                    style={[styles.input, {
                      backgroundColor: palette.surface.card, color: palette.text.primary,
                      borderColor: fieldState.error ? '#EF4444' : palette.surface.border,
                    }]}
                    placeholder={field === 'displayName' ? 'Optional' : `Enter ${field}`}
                    placeholderTextColor={palette.text.tertiary}
                    secureTextEntry={field === 'password'}
                    autoCapitalize="none"
                    value={f.value}
                    onChangeText={f.onChange}
                  />
                </View>
              )}
            />
          ))}

          <TouchableOpacity
            style={[styles.button, isLoading && styles.buttonDisabled]}
            onPress={handleSubmit(onSubmit)}
            disabled={isLoading}
          >
            {isLoading ? <ActivityIndicator color="#FFF" /> : <Text style={styles.buttonText}>Create Account</Text>}
          </TouchableOpacity>

          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.footer}>
            <Text style={{ color: palette.text.secondary }}>
              Already have an account?{' '}
              <Text style={{ color: palette.primary[400], fontWeight: '600' }}>Sign in</Text>
            </Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 }, flex: { flex: 1 },
  container: { padding: spacing.xl, paddingBottom: 40 },
  title: { fontSize: 32, fontWeight: '700', marginBottom: 4 },
  subtitle: { fontSize: 16, marginBottom: 24 },
  error: { color: '#EF4444', backgroundColor: '#FEF2F2', padding: 12, borderRadius: radius.sm, marginBottom: 16 },
  field: { marginBottom: spacing.md },
  label: { fontSize: 14, fontWeight: '500', marginBottom: 6 },
  input: { height: 48, borderWidth: 1, borderRadius: radius.md, paddingHorizontal: 14, fontSize: 16 },
  button: { backgroundColor: '#3B82F6', height: 52, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center', marginTop: spacing.lg },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#FFF', fontSize: 16, fontWeight: '600' },
  footer: { alignItems: 'center', marginTop: spacing.xl },
});
