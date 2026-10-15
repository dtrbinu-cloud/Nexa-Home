import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_button.dart';
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
  final List<TextEditingController> _controllers = List.generate(6, (_) => TextEditingController());
  final List<FocusNode> _focusNodes = List.generate(6, (_) => FocusNode());
  final _backupCodeController = TextEditingController();
  bool _useRecoveryCode = false;

  @override
  void dispose() {
    for (final c in _controllers) {
      c.dispose();
    }
    for (final f in _focusNodes) {
      f.dispose();
    }
    _backupCodeController.dispose();
    super.dispose();
  }

  String _getEnteredCode() {
    if (_useRecoveryCode) {
      return _backupCodeController.text.trim();
    }
    return _controllers.map((c) => c.text).join();
  }

  Future<void> _handleVerify() async {
    final code = _getEnteredCode();
    if (code.isEmpty || (!_useRecoveryCode && code.length < 6)) {
      AppToast.show(
        context,
        _useRecoveryCode ? 'Masukkan kode cadangan.' : 'Masukkan 6 digit kode verifikasi.',
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
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkBg : AppColors.lightBg;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;
    final subtle = isDark ? AppColors.darkSubtle : AppColors.lightSubtle;

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
              const SizedBox(height: AppSpacing.space3),

              // Back button
              IconButton(
                icon: PhosphorIcon(PhosphorIcons.arrowLeft(), size: AppDimensions.iconSizeMd, color: text),
                tooltip: 'Kembali ke login',
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
                onPressed: () {
                  ref.read(authProvider.notifier).logout();
                  context.go('/login');
                },
              ),

              const SizedBox(height: AppSpacing.space6),

              // Title "Kode verifikasi" (32/600)
              Text(
                'Kode verifikasi',
                style: AppTypography.body(
                  text,
                  size: AppTypography.textXl, // 32px
                  weight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: AppSpacing.space2),
              Text(
                _useRecoveryCode
                    ? 'Masukkan kode cadangan 8 karakter Anda.'
                    : 'Masukkan 6 digit dari aplikasi autentikator.',
                style: AppTypography.body(textSec, size: AppTypography.textSm),
              ),

              const SizedBox(height: AppDimensions.sectionGap * 1.5),

              if (_useRecoveryCode)
                AppInput(
                  hint: 'Kode cadangan',
                  controller: _backupCodeController,
                  isMono: true,
                )
              else
                // 6 Digit Input Boxes (fill subtle, radius 12, outline 2px accent when focused)
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: List.generate(6, (index) {
                    return SizedBox(
                      width: 44,
                      height: 54,
                      child: TextField(
                        controller: _controllers[index],
                        focusNode: _focusNodes[index],
                        keyboardType: TextInputType.number,
                        textAlign: TextAlign.center,
                        maxLength: 1,
                        cursorColor: accent,
                        style: AppTypography.mono(
                          text,
                          size: AppTypography.textLg,
                          weight: FontWeight.w600,
                        ),
                        decoration: InputDecoration(
                          counterText: '',
                          filled: true,
                          fillColor: subtle,
                          contentPadding: EdgeInsets.zero,
                          enabledBorder: const OutlineInputBorder(
                            borderRadius: AppRadius.borderSm,
                            borderSide: BorderSide.none,
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: AppRadius.borderSm,
                            borderSide: BorderSide(
                              color: accent,
                              width: 2.0,
                            ),
                          ),
                        ),
                        onChanged: (val) {
                          if (val.isNotEmpty && index < 5) {
                            _focusNodes[index + 1].requestFocus();
                          } else if (val.isEmpty && index > 0) {
                            _focusNodes[index - 1].requestFocus();
                          }
                          if (_getEnteredCode().length == 6) {
                            _handleVerify();
                          }
                        },
                      ),
                    );
                  }),
                ),

              const SizedBox(height: AppDimensions.sectionGap * 1.5),

              // Tombol Verifikasi (48px, radius 12, accent)
              AppButton(
                label: 'Verifikasi',
                isLoading: isLoading,
                onPressed: _handleVerify,
              ),

              const SizedBox(height: AppSpacing.space4),

              // Link Pakai kode cadangan
              Center(
                child: TextButton(
                  onPressed: () {
                    setState(() => _useRecoveryCode = !_useRecoveryCode);
                  },
                  child: Text(
                    _useRecoveryCode ? 'Pakai kode autentikator' : 'Pakai kode cadangan',
                    style: AppTypography.body(
                      accent,
                      size: AppTypography.textSm,
                      weight: FontWeight.w600,
                    ),
                  ),
                ),
              ),

              const SizedBox(height: AppSpacing.space6),
            ],
          ),
        ),
      ),
    );
  }
}
