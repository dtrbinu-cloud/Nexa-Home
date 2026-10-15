import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:local_auth/local_auth.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_button.dart';
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
  final _serverUrlController = TextEditingController();

  bool _obscurePassword = true;
  bool _showServerConfig = false;
  final _localAuth = LocalAuthentication();
  bool _canCheckBiometrics = false;

  @override
  void initState() {
    super.initState();
    _checkBiometrics();
    StorageService.getUsername().then((saved) {
      if (saved != null && saved.isNotEmpty && mounted) {
        _usernameController.text = saved;
      }
    });
    StorageService.getServerUrl().then((url) {
      if (mounted) _serverUrlController.text = url;
    });
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _serverUrlController.dispose();
    super.dispose();
  }

  Future<void> _checkBiometrics() async {
    try {
      final isEnabled = await StorageService.isBiometricEnabled();
      if (isEnabled) {
        final canCheck = await _localAuth.canCheckBiometrics;
        if (mounted) setState(() => _canCheckBiometrics = canCheck);
      }
    } catch (_) {}
  }

  Future<void> _handleLogin() async {
    final username = _usernameController.text.trim();
    final password = _passwordController.text;

    if (username.isEmpty || password.isEmpty) {
      AppToast.show(context, 'Masukkan nama pengguna dan kata sandi.', isError: true);
      return;
    }

    if (_showServerConfig && _serverUrlController.text.trim().isNotEmpty) {
      await StorageService.setServerUrl(_serverUrlController.text.trim());
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

  Future<void> _handleBiometricLogin() async {
    try {
      final didAuth = await _localAuth.authenticate(
        localizedReason: 'Pindai sidik jari untuk masuk ke Rumah',
      );
      if (didAuth && mounted) {
        final token = await StorageService.getAccessToken();
        if (token != null && token.isNotEmpty) {
          ref.read(authProvider.notifier).init();
        }
      }
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkBg : AppColors.lightBg;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;

    final auth = ref.watch(authProvider);
    final isLoading = auth.isLoading;

    return Scaffold(
      backgroundColor: bg,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMarginAuth), // 24px
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: AppSpacing.space6),

              // House icon + "Rumah"
              Row(
                children: [
                  PhosphorIcon(
                    PhosphorIcons.house(PhosphorIconsStyle.fill),
                    size: AppDimensions.iconSizeMd,
                    color: accent,
                  ),
                  const SizedBox(width: AppSpacing.space2),
                  Text(
                    'Rumah',
                    style: AppTypography.body(
                      text,
                      size: AppTypography.textMd,
                      weight: FontWeight.w600,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: AppSpacing.space8),

              // Title "Masuk" 32/600
              Text(
                'Masuk',
                style: AppTypography.body(
                  text,
                  size: AppTypography.textXl, // 32px
                  weight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: AppSpacing.space2),
              Text(
                'Gunakan akun dari admin rumah.',
                style: AppTypography.body(textSec, size: AppTypography.textSm),
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              // Form Input Nama Pengguna
              AppInput(
                hint: 'Nama pengguna',
                controller: _usernameController,
              ),

              const SizedBox(height: AppDimensions.cardGap),

              // Form Input Kata Sandi
              AppInput(
                hint: 'Kata sandi',
                controller: _passwordController,
                obscureText: _obscurePassword,
                suffixIcon: IconButton(
                  icon: PhosphorIcon(
                    _obscurePassword ? PhosphorIcons.eye() : PhosphorIcons.eyeSlash(),
                    size: AppDimensions.iconSizeSm,
                    color: textSec,
                  ),
                  onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                ),
              ),

              const SizedBox(height: AppSpacing.space3),

              // Subtext: Lupa kata sandi? Minta admin mengatur ulang.
              Text(
                'Lupa kata sandi? Minta admin mengatur ulang.',
                style: AppTypography.body(textSec, size: AppTypography.textXs),
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              // Tombol Masuk (Accent, 48px, radius 12)
              AppButton(
                label: 'Masuk',
                isLoading: isLoading,
                onPressed: _handleLogin,
              ),

              if (_canCheckBiometrics) ...[
                const SizedBox(height: AppSpacing.space3),
                AppButton(
                  label: 'Masuk dengan Sidik Jari',
                  variant: AppButtonVariant.secondary,
                  onPressed: _handleBiometricLogin,
                ),
              ],

              const SizedBox(height: AppSpacing.space4),

              // Server URL Config Toggle (Opsional / Terbuka jika diperlukan)
              Center(
                child: TextButton(
                  onPressed: () => setState(() => _showServerConfig = !_showServerConfig),
                  child: Text(
                    _showServerConfig ? 'Sembunyikan Pengaturan Server' : 'Atur Alamat Server',
                    style: AppTypography.body(textSec, size: AppTypography.textXs),
                  ),
                ),
              ),

              if (_showServerConfig) ...[
                const SizedBox(height: AppSpacing.space2),
                AppInput(
                  label: 'Alamat Server',
                  controller: _serverUrlController,
                  hint: 'https://aujasena.my.id',
                ),
              ],

              const SizedBox(height: AppSpacing.space6),
            ],
          ),
        ),
      ),
    );
  }
}
