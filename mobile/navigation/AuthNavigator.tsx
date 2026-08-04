/** Auth navigator — login, register, forgot/reset password */

import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

const Stack = createNativeStackNavigator();

export function AuthNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        animation: 'slide_from_right',
        contentStyle: { backgroundColor: '#0A0A0A' },
      }}
    >
      <Stack.Screen name="login" getComponent={() => require('@/components/auth/LoginScreen').LoginScreen} />
      <Stack.Screen name="register" getComponent={() => require('@/components/auth/RegisterScreen').RegisterScreen} />
      <Stack.Screen name="forgotPassword" getComponent={() => require('@/components/auth/PasswordScreens').ForgotPasswordScreen} />
      <Stack.Screen name="resetPassword" getComponent={() => require('@/components/auth/PasswordScreens').ResetPasswordScreen} />
      <Stack.Screen name="verifyEmail" getComponent={() => require('@/components/auth/PasswordScreens').VerifyEmailScreen} />
    </Stack.Navigator>
  );
}
