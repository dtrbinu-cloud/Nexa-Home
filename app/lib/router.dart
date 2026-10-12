import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:app/core/auth_state.dart';
import 'package:app/screens/design_screen.dart';
import 'package:app/screens/login_screen.dart';
import 'package:app/screens/setup_wizard_screen.dart';
import 'package:app/screens/shell_screen.dart';
import 'package:app/screens/tabs/settings_tab.dart';
import 'package:app/screens/verify_2fa_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final auth = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/',
    redirect: (BuildContext context, GoRouterState state) {
      final loc = state.matchedLocation;

      if (auth.status == AuthStatus.needsSetup) {
        if (loc != '/setup') return '/setup';
        return null;
      }

      if (auth.status == AuthStatus.twoFactorPending) {
        if (loc != '/verify-2fa') return '/verify-2fa';
        return null;
      }

      if (auth.status == AuthStatus.unauthenticated) {
        if (loc != '/login' && loc != '/setup' && loc != '/settings') return '/login';
        return null;
      }

      if (auth.status == AuthStatus.authenticated) {
        if (loc == '/login' || loc == '/setup' || loc == '/verify-2fa') return '/';
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => const ShellScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/setup',
        builder: (context, state) => const SetupWizardScreen(),
      ),
      GoRoute(
        path: '/verify-2fa',
        builder: (context, state) => const Verify2FAScreen(),
      ),
      GoRoute(
        path: '/settings',
        builder: (context, state) => const SettingsTab(),
      ),
      GoRoute(
        path: '/design',
        builder: (context, state) => const DesignScreen(),
      ),
    ],
  );
});
