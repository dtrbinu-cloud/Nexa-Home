import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_input.dart';
import 'package:app/components/app_toast.dart';
import 'package:app/core/auth_state.dart';
import 'package:app/theme/tokens.dart';

class Verify2FAScreen extends ConsumerStatefulWidget {
  const Verify2FAScreen({super.key});

  @override
  ConsumerState<Verify2FAScreen> createState() => _Verify2FAScreenState();
}

class _Verify2FAScreenState extends ConsumerState<Verify2FAScreen> {
  final _codeController = TextEditingController();
  bool _useRecoveryCode = false;

  Future<void> _handleVerify() async {
    final code = _codeController.text.trim();
    if (code.isEmpty) {
      AppToast.show(
        context,
        _useRecoveryCode ? 'Masukkan kode pemulihan.' : 'Masukkan 6-digit kode TOTP.',
        isError: true,
      );
      return;
    }

    final success = await ref.read(authProvider.notifier).verify2FA(code);
    if (!mounted) return;

    final state = ref.read(authProvider);
    if (success && state.status == AuthStatus.authenticated) {
      context.go('/');
    } else if (state.errorMessage != null) {
      AppToast.show(context, state.errorMessage!, isError: true);
    }
  }

  @override
  void dispose() {
    _codeController.dispose();
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
        title: const Text('Verifikasi Dua Langkah'),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(AppSpacing.space4),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Icon(
                  _useRecoveryCode ? PhosphorIcons.lifebuoy() : PhosphorIcons.shieldCheck(),
                  size: AppDimensions.iconSizeMd * 2,
                  color: isDark ? AppColors.darkAccent : AppColors.lightAccent,
                ),
                const SizedBox(height: AppSpacing.space3),
                Text(
                  _useRecoveryCode ? 'Kode Pemulihan Cadangan' : 'Kode Autentikasi TOTP',
                  style: AppTypography.body(
                    text,
                    size: AppTypography.textLg,
                    weight: FontWeight.w700,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: AppSpacing.space1),
                Text(
                  _useRecoveryCode
                      ? 'Masukkan salah satu dari 8 kode pemulihan (format: XXXX-XXXX).'
                      : 'Buka aplikasi authenticator dan masukkan 6-digit kode saat ini.',
                  style: AppTypography.body(textSec, size: AppTypography.textSm),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: AppSpacing.space6),
                AppCard(
                  child: Column(
                    children: [
                      AppInput(
                        label: _useRecoveryCode ? 'Kode Pemulihan' : '6 Digit Kode TOTP',
                        hint: _useRecoveryCode ? 'Contoh: 4F2A-9B1C' : '123456',
                        controller: _codeController,
                        keyboardType: _useRecoveryCode
                            ? TextInputType.text
                            : TextInputType.number,
                        autofocus: true,
                        prefixIcon: Icon(
                          PhosphorIcons.key(),
                          size: AppDimensions.iconSizeSm,
                          color: textSec,
                        ),
                      ),
                      const SizedBox(height: AppSpacing.space4),
                      AppButton(
                        label: 'Verifikasi & Masuk',
                        onPressed: _handleVerify,
                        isLoading: auth.isLoading,
                        icon: Icon(
                          PhosphorIcons.check(),
                          size: AppDimensions.iconSizeSm,
                          color: AppColors.lightSurface,
                        ),
                      ),
                      const SizedBox(height: AppSpacing.space3),
                      AppButton(
                        label: _useRecoveryCode
                            ? 'Kembali ke Kode TOTP'
                            : 'Gunakan Kode Pemulihan Cadangan',
                        variant: AppButtonVariant.secondary,
                        onPressed: () {
                          setState(() {
                            _useRecoveryCode = !_useRecoveryCode;
                            _codeController.clear();
                          });
                        },
                      ),
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
