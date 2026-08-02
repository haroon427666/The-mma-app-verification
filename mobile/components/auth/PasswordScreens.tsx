/** Forgot Password + Reset Password screens */

import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { authService } from '@/services/auth';
import { useTheme } from '@/hooks/useTheme';
import { spacing, radius } from '@/theme';

export function ForgotPasswordScreen({ navigation }: any) {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const { palette } = useTheme();

  const handleSend = async () => {
    if (!email.trim()) return;
    setLoading(true);
    try { await authService.forgotPassword(email); setSent(true); }
    catch { /* Don't reveal if email exists */ setSent(true); }
    finally { setLoading(false); }
  };

  if (sent) {
    return (
      <SafeAreaView style={[styles.root, { backgroundColor: palette.surface.bg }]}>
        <View style={styles.container}>
          <Text style={styles.icon}>✉️</Text>
          <Text style={[styles.title, { color: palette.text.primary }]}>Check your email</Text>
          <Text style={[styles.subtitle, { color: palette.text.secondary }]}>
            We sent a reset link to {email}. It expires in 1 hour.
          </Text>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.buttonOutlined}>
            <Text style={[styles.buttonOutlinedText, { color: palette.primary[400] }]}>Back to login</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.root, { backgroundColor: palette.surface.bg }]}>
      <View style={styles.container}>
        <Text style={[styles.title, { color: palette.text.primary }]}>Reset password</Text>
        <Text style={[styles.subtitle, { color: palette.text.secondary }]}>Enter your email to receive a reset link</Text>
        <TextInput style={[styles.input, { backgroundColor: palette.surface.card, color: palette.text.primary, borderColor: palette.surface.border }]}
          placeholder="you@example.com" placeholderTextColor={palette.text.tertiary}
          value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" />
        <TouchableOpacity style={styles.button} onPress={handleSend} disabled={loading}>
          {loading ? <ActivityIndicator color="#FFF" /> : <Text style={styles.buttonText}>Send reset link</Text>}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

export function ResetPasswordScreen({ route, navigation }: any) {
  const [password, setPassword] = useState('');
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);
  const { palette } = useTheme();
  const token = route?.params?.token || '';

  const handleReset = async () => {
    if (password.length < 8) return;
    setLoading(true);
    try { await authService.resetPassword(token, password); setDone(true); }
    catch { /* error handling */ }
    finally { setLoading(false); }
  };

  if (done) {
    return (
      <SafeAreaView style={[styles.root, { backgroundColor: palette.surface.bg }]}>
        <View style={styles.container}>
          <Text style={styles.icon}>🔐</Text>
          <Text style={[styles.title, { color: palette.text.primary }]}>Password reset</Text>
          <Text style={[styles.subtitle, { color: palette.text.secondary }]}>Your password has been changed. Please log in.</Text>
          <TouchableOpacity onPress={() => navigation.navigate('login')} style={styles.button}>
            <Text style={styles.buttonText}>Go to login</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.root, { backgroundColor: palette.surface.bg }]}>
      <View style={styles.container}>
        <Text style={[styles.title, { color: palette.text.primary }]}>New password</Text>
        <TextInput style={[styles.input, { backgroundColor: palette.surface.card, color: palette.text.primary, borderColor: palette.surface.border }]}
          placeholder="Min 8 characters" placeholderTextColor={palette.text.tertiary}
          value={password} onChangeText={setPassword} secureTextEntry />
        <TouchableOpacity style={styles.button} onPress={handleReset} disabled={loading}>
          {loading ? <ActivityIndicator color="#FFF" /> : <Text style={styles.buttonText}>Reset password</Text>}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

export function VerifyEmailScreen({ route, navigation }: any) {
  const [verified, setVerified] = useState(false);
  const { palette } = useTheme();
  const token = route?.params?.token || '';

  React.useEffect(() => {
    (async () => {
      try { await authService.verifyEmail(token); setVerified(true); }
      catch { /* stay on screen */ }
    })();
  }, [token]);

  return (
    <SafeAreaView style={[styles.root, { backgroundColor: palette.surface.bg }]}>
      <View style={styles.container}>
        <Text style={styles.icon}>{verified ? '✅' : '⏳'}</Text>
        <Text style={[styles.title, { color: palette.text.primary }]}>
          {verified ? 'Email verified!' : 'Verifying...'}
        </Text>
        {verified && (
          <TouchableOpacity onPress={() => navigation.navigate('login')} style={styles.button}>
            <Text style={styles.buttonText}>Continue to login</Text>
          </TouchableOpacity>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  container: { flex: 1, padding: spacing.xl, justifyContent: 'center' },
  icon: { fontSize: 48, textAlign: 'center', marginBottom: 16 },
  title: { fontSize: 28, fontWeight: '700', marginBottom: 8 },
  subtitle: { fontSize: 16, marginBottom: 24 },
  input: { height: 48, borderWidth: 1, borderRadius: radius.md, paddingHorizontal: 14, fontSize: 16, marginBottom: spacing.lg },
  button: { backgroundColor: '#3B82F6', height: 52, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center' },
  buttonText: { color: '#FFF', fontSize: 16, fontWeight: '600' },
  buttonOutlined: { height: 52, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#3B82F6', marginTop: spacing.lg },
  buttonOutlinedText: { fontSize: 16, fontWeight: '600' },
});
