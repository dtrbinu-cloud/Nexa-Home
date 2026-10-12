import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:local_auth/local_auth.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_input.dart';
import 'package:app/components/app_switch.dart';
import 'package:app/components/app_toast.dart';
import 'package:app/core/api_client.dart';
import 'package:app/core/auth_state.dart';
import 'package:app/core/storage.dart';
import 'package:app/theme/tokens.dart';

class SettingsTab extends ConsumerStatefulWidget {
  const SettingsTab({super.key});

  @override
  ConsumerState<SettingsTab> createState() => _SettingsTabState();
}

class _SettingsTabState extends ConsumerState<SettingsTab> {
  final _urlController = TextEditingController();
  bool _biometricEnabled = false;

  @override
  void initState() {
    super.initState();
    StorageService.getServerUrl().then((url) => _urlController.text = url);
    StorageService.isBiometricEnabled().then((b) => setState(() => _biometricEnabled = b));
  }

  Future<void> _saveUrl() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) return;
    await StorageService.setServerUrl(url);
    ApiClient.reset();
    if (mounted) {
      AppToast.show(context, 'Alamat server berhasil disimpan.');
    }
  }

  Future<void> _toggleBiometric(bool val) async {
    if (val) {
      final auth = LocalAuthentication();
      final canCheck = await auth.canCheckBiometrics;
      if (!canCheck) {
        if (mounted) {
          AppToast.show(context, 'Perangkat tidak mendukung biometrik.', isError: true);
        }
        return;
      }
    }
    await StorageService.setBiometricEnabled(val);
    if (!mounted) return;
    setState(() => _biometricEnabled = val);
    AppToast.show(context, val ? 'Kunci biometrik diaktifkan.' : 'Kunci biometrik dinonaktifkan.');
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final currentTheme = ref.watch(themeModeProvider);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Icon(
              PhosphorIcons.gear(),
              size: AppDimensions.iconSizeSm,
              color: text,
            ),
            const SizedBox(width: AppSpacing.space2),
            const Text('Pengaturan'),
          ],
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.space4),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Koneksi Server',
                style: AppTypography.body(
                  text,
                  size: AppTypography.textMd,
                  weight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: AppSpacing.space2),
              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AppInput(
                      label: 'Alamat Server Backend',
                      hint: 'http://192.168.1.10:8000',
                      controller: _urlController,
                      prefixIcon: Icon(
                        PhosphorIcons.globe(),
                        size: AppDimensions.iconSizeSm,
                        color: textSec,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.space3),
                    AppButton(
                      label: 'Simpan Alamat Server',
                      variant: AppButtonVariant.secondary,
                      onPressed: _saveUrl,
                      icon: Icon(
                        PhosphorIcons.floppyDisk(),
                        size: AppDimensions.iconSizeSm,
                        color: text,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.space4),
              Text(
                'Preferensi Aplikasi',
                style: AppTypography.body(
                  text,
                  size: AppTypography.textMd,
                  weight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: AppSpacing.space2),
              AppCard(
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            Icon(
                              currentTheme == 'dark' ? PhosphorIcons.moon() : PhosphorIcons.sun(),
                              size: AppDimensions.iconSizeSm,
                              color: text,
                            ),
                            const SizedBox(width: AppSpacing.space2),
                            Text(
                              'Mode Gelap',
                              style: AppTypography.body(text, size: AppTypography.textSm),
                            ),
                          ],
                        ),
                        AppSwitch(
                          value: currentTheme == 'dark',
                          onChanged: (_) => ref.read(themeModeProvider.notifier).toggle(),
                        ),
                      ],
                    ),
                    const Divider(height: AppSpacing.space6),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            Icon(
                              PhosphorIcons.fingerprint(),
                              size: AppDimensions.iconSizeSm,
                              color: text,
                            ),
                            const SizedBox(width: AppSpacing.space2),
                            Text(
                              'Kunci Biometrik',
                              style: AppTypography.body(text, size: AppTypography.textSm),
                            ),
                          ],
                        ),
                        AppSwitch(
                          value: _biometricEnabled,
                          onChanged: _toggleBiometric,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.space4),
              if (kDebugMode) ...[
                Text(
                  'Pengembang (Mode Debug)',
                  style: AppTypography.body(
                    text,
                    size: AppTypography.textMd,
                    weight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: AppSpacing.space2),
                AppCard(
                  child: AppButton(
                    label: 'Katalog Desain & Token (DesignScreen)',
                    variant: AppButtonVariant.secondary,
                    onPressed: () => context.push('/design'),
                    icon: Icon(
                      PhosphorIcons.palette(),
                      size: AppDimensions.iconSizeSm,
                      color: text,
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.space4),
              ],
              Text(
                'Sesi Akun',
                style: AppTypography.body(
                  text,
                  size: AppTypography.textMd,
                  weight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: AppSpacing.space2),
              AppCard(
                child: AppButton(
                  label: 'Keluar dari Akun',
                  variant: AppButtonVariant.danger,
                  onPressed: () async {
                    await ref.read(authProvider.notifier).logout();
                    if (context.mounted) {
                      context.go('/login');
                    }
                  },
                  icon: Icon(
                    PhosphorIcons.signOut(),
                    size: AppDimensions.iconSizeSm,
                    color: AppColors.lightSurface,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
