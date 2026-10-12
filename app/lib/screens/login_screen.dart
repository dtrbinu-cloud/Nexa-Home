import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:local_auth/local_auth.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_input.dart';
import 'package:app/components/app_toast.dart';
import 'package:app/core/auth_state.dart';
import 'package:app/core/storage.dart';
import 'package:app/theme/tokens.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _localAuth = LocalAuthentication();
  bool _canCheckBiometrics = false;

  @override
  void initState() {
    super.initState();
    _checkBiometrics();
    StorageService.getUsername().then((saved) {
      if (saved != null && saved.isNotEmpty) {
        _usernameController.text = saved;
      }
    });
  }

  Future<void> _checkBiometrics() async {
    try {
      final isEnabled = await StorageService.isBiometricEnabled();
      if (isEnabled) {
        final canCheck = await _localAuth.canCheckBiometrics;
        setState(() => _canCheckBiometrics = canCheck);
      }
    } catch (_) {}
  }

  Future<void> _handleBiometricAuth() async {
    try {
      final authenticated = await _localAuth.authenticate(
        localizedReason: 'Pindai sidik jari atau wajah untuk masuk ke Rumah',
      );
      if (authenticated) {
        final savedUser = await StorageService.getUsername();
        if (savedUser != null && mounted) {
          AppToast.show(context, 'Biometrik terverifikasi.');
        }
      }
    } catch (_) {
      if (mounted) {
        AppToast.show(context, 'Gagal memverifikasi biometrik.', isError: true);
      }
    }
  }

  Future<void> _handleLogin() async {
    final username = _usernameController.text.trim();
    final password = _passwordController.text;

    if (username.isEmpty || password.isEmpty) {
      AppToast.show(context, 'Masukkan nama pengguna dan kata sandi.', isError: true);
      return;
    }

    final success = await ref.read(authProvider.notifier).login(username, password);
    if (!mounted) return;

    final state = ref.read(authProvider);
    if (success) {
      if (state.status == AuthStatus.twoFactorPending) {
        context.go('/verify-2fa');
      } else if (state.status == AuthStatus.authenticated) {
        context.go('/');
      }
    } else if (state.errorMessage != null) {
      AppToast.show(context, state.errorMessage!, isError: true);
    }
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final auth = ref.watch(authProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Masuk ke Rumah'),
        actions: [
          IconButton(
            icon: Icon(
              PhosphorIcons.gear(),
              size: AppDimensions.iconSizeSm,
              color: text,
            ),
            onPressed: () => context.push('/settings'),
            tooltip: 'Pengaturan Server',
          ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(AppSpacing.space4),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Icon(
                  PhosphorIcons.house(),
                  size: AppDimensions.iconSizeMd * 2,
                  color: isDark ? AppColors.darkAccent : AppColors.lightAccent,
                ),
                const SizedBox(height: AppSpacing.space3),
                Text(
                  'Rumah',
                  style: AppTypography.body(
                    text,
                    size: AppTypography.textXl,
                    weight: FontWeight.w700,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: AppSpacing.space1),
                Text(
                  'Sistem Smart Home & Pengawasan Keluarga',
                  style: AppTypography.body(textSec, size: AppTypography.textSm),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: AppSpacing.space6),
                AppCard(
                  child: Column(
                    children: [
                      AppInput(
                        label: 'Nama Pengguna',
                        hint: 'admin / member / child',
                        controller: _usernameController,
                        prefixIcon: Icon(
                          PhosphorIcons.user(),
                          size: AppDimensions.iconSizeSm,
                          color: textSec,
                        ),
                      ),
                      const SizedBox(height: AppSpacing.space3),
                      AppInput(
                        label: 'Kata Sandi',
                        hint: '••••••••',
                        obscureText: true,
                        controller: _passwordController,
                        prefixIcon: Icon(
                          PhosphorIcons.lock(),
                          size: AppDimensions.iconSizeSm,
                          color: textSec,
                        ),
                      ),
                      const SizedBox(height: AppSpacing.space4),
                      AppButton(
                        label: 'Masuk',
                        onPressed: _handleLogin,
                        isLoading: auth.isLoading,
                        icon: Icon(
                          PhosphorIcons.signIn(),
                          size: AppDimensions.iconSizeSm,
                          color: AppColors.lightSurface,
                        ),
                      ),
                      if (_canCheckBiometrics) ...[
                        const SizedBox(height: AppSpacing.space3),
                        AppButton(
                          label: 'Masuk dengan Biometrik',
                          variant: AppButtonVariant.secondary,
                          onPressed: _handleBiometricAuth,
                          icon: Icon(
                            PhosphorIcons.fingerprint(),
                            size: AppDimensions.iconSizeSm,
                            color: text,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
