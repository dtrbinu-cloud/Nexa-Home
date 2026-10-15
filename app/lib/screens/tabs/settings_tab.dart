import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:local_auth/local_auth.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_badge.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_input.dart';
import 'package:app/components/app_switch.dart';
import 'package:app/components/app_toast.dart';
import 'package:app/core/api_client.dart';
import 'package:app/core/auth_state.dart';
import 'package:app/core/network_validator.dart';
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
  String _selectedVoice = 'id-ID-ArdiNeural';
  bool _ttsAutoPlay = true;

  @override
  void initState() {
    super.initState();
    StorageService.getServerUrl().then((url) => _urlController.text = url);
    StorageService.isBiometricEnabled().then((b) => setState(() => _biometricEnabled = b));
    StorageService.getTtsVoice().then((v) => setState(() => _selectedVoice = v));
    StorageService.isTtsAutoPlay().then((b) => setState(() => _ttsAutoPlay = b));
  }

  Future<void> _saveUrl() async {
    final url = _urlController.text.trim();
    final err = NetworkValidator.validateServerUrl(url);
    if (err != null) {
      if (mounted) {
        AppToast.show(context, err, isError: true);
      }
      return;
    }

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

  void _showLinkGoogleModal() {
    final tokenController = TextEditingController(text: 'mock_google_id_token_budi');
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: isDark ? AppColors.darkSurface : AppColors.lightSurface,
        shape: const RoundedRectangleBorder(
          borderRadius: AppRadius.borderMd,
          side: BorderSide(
            color: AppColors.darkBorder,
            width: AppDimensions.borderWidth,
          ),
        ),
        title: Text(
          'Tautkan Akun Google',
          style: AppTypography.body(text, size: AppTypography.textMd, weight: FontWeight.w600),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Masukkan ID Token akun Google Anda untuk menautkan akun Rumah ini dengan Google:',
              style: AppTypography.body(textSec, size: AppTypography.textSm),
            ),
            const SizedBox(height: AppSpacing.space3),
            AppInput(
              label: 'Google ID Token / Dev Token',
              hint: 'mock_google_id_token_...',
              controller: tokenController,
            ),
            const SizedBox(height: AppSpacing.space2),
            Text(
              'Simulasi dev: gunakan mock_google_id_token_budi',
              style: AppTypography.mono(textSec, size: AppTypography.textXs),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text('Batal', style: AppTypography.body(textSec)),
          ),
          AppButton(
            label: 'Tautkan Sekarang',
            isFullWidth: false,
            onPressed: () async {
              Navigator.of(ctx).pop();
              final token = tokenController.text.trim();
              if (token.isEmpty) return;

              final err = await ref.read(authProvider.notifier).linkGoogle(token);
              if (!mounted) return;
              if (err == null) {
                AppToast.show(context, 'Akun Google berhasil ditautkan.');
              } else {
                AppToast.show(context, err, isError: true);
              }
            },
          ),
        ],
      ),
    );
  }

  void _handleUnlinkGoogle() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: isDark ? AppColors.darkSurface : AppColors.lightSurface,
        shape: const RoundedRectangleBorder(
          borderRadius: AppRadius.borderMd,
          side: BorderSide(
            color: AppColors.darkBorder,
            width: AppDimensions.borderWidth,
          ),
        ),
        title: Text(
          'Lepas Tautan Akun Google?',
          style: AppTypography.body(text, size: AppTypography.textMd, weight: FontWeight.w600),
        ),
        content: Text(
          'Setelah dilepas, Anda hanya bisa masuk menggunakan username atau email beserta kata sandi manual.',
          style: AppTypography.body(textSec, size: AppTypography.textSm),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text('Batal', style: AppTypography.body(textSec)),
          ),
          AppButton(
            label: 'Lepas Tautan',
            variant: AppButtonVariant.danger,
            isFullWidth: false,
            onPressed: () async {
              Navigator.of(ctx).pop();
              final err = await ref.read(authProvider.notifier).unlinkGoogle();
              if (!mounted) return;
              if (err == null) {
                AppToast.show(context, 'Tautan akun Google telah dilepas.');
              } else {
                AppToast.show(context, err, isError: true);
              }
            },
          ),
        ],
      ),
    );
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
    final auth = ref.watch(authProvider);

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
              Text(
                'Asisten Percakapan & Suara',
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
                    Text(
                      'Pilihan Suara Asisten (TTS)',
                      style: AppTypography.body(text, size: AppTypography.textSm, weight: FontWeight.w600),
                    ),
                    const SizedBox(height: AppSpacing.space2),
                    DropdownButtonFormField<String>(
                      initialValue: _selectedVoice,
                      dropdownColor: isDark ? AppColors.darkSurface : AppColors.lightSurface,
                      decoration: InputDecoration(
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: AppSpacing.space3,
                          vertical: AppSpacing.space2,
                        ),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(AppRadius.md),
                          borderSide: BorderSide(
                            color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                          ),
                        ),
                      ),
                      style: AppTypography.body(text, size: AppTypography.textSm),
                      items: [
                        DropdownMenuItem(
                          value: 'id-ID-ArdiNeural',
                          child: Text('Ardi (Pria) — Online Edge TTS', style: AppTypography.body(text)),
                        ),
                        DropdownMenuItem(
                          value: 'id-ID-GadisNeural',
                          child: Text('Gadis (Wanita) — Online Edge TTS', style: AppTypography.body(text)),
                        ),
                        DropdownMenuItem(
                          value: 'id_ID-indotts-medium',
                          child: Text('Piper Indonesia — Offline Lokal', style: AppTypography.body(text)),
                        ),
                      ],
                      onChanged: (val) async {
                        if (val != null) {
                          setState(() => _selectedVoice = val);
                          await StorageService.setTtsVoice(val);
                        }
                      },
                    ),
                    const Divider(height: AppSpacing.space6),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Putar Suara Balasan (TTS)',
                              style: AppTypography.body(text, size: AppTypography.textSm, weight: FontWeight.w500),
                            ),
                            Text(
                              'Otomatis membacakan balasan asisten',
                              style: AppTypography.body(textSec, size: AppTypography.textXs),
                            ),
                          ],
                        ),
                        AppSwitch(
                          value: _ttsAutoPlay,
                          onChanged: (val) async {
                            setState(() => _ttsAutoPlay = val);
                            await StorageService.setTtsAutoPlay(val);
                          },
                        ),
                      ],
                    ),
                    const Divider(height: AppSpacing.space6),
                    Container(
                      padding: const EdgeInsets.all(AppSpacing.space3),
                      decoration: BoxDecoration(
                        color: isDark ? AppColors.darkSurface : AppColors.lightSurface,
                        borderRadius: BorderRadius.circular(AppRadius.sm),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(
                            PhosphorIcons.shieldCheck(),
                            size: AppDimensions.iconSizeSm,
                            color: isDark ? AppColors.darkAccent : AppColors.lightAccent,
                          ),
                          const SizedBox(width: AppSpacing.space2),
                          Expanded(
                            child: Text(
                              'Catatan Privasi STT: Pada sebagian besar perangkat Android, pemrosesan pengenalan suara dilakukan oleh layanan suara Google.',
                              style: AppTypography.body(textSec, size: AppTypography.textXs),
                            ),
                          ),
                        ],
                      ),
                    ),

                  ],
                ),
              ),
              if (ref.watch(authProvider).role == 'admin') ...[
                const SizedBox(height: AppSpacing.space4),
                Text(
                  'Administrasi Sistem',
                  style: AppTypography.body(
                    text,
                    size: AppTypography.textMd,
                    weight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: AppSpacing.space2),
                AppCard(
                  child: AppButton(
                    label: 'Kelola Alias & Izin Kanal Anak',
                    variant: AppButtonVariant.secondary,
                    onPressed: () => context.push('/channel-admin'),
                    icon: Icon(
                      PhosphorIcons.slidersHorizontal(),
                      size: AppDimensions.iconSizeSm,
                      color: text,
                    ),
                  ),
                ),
              ],
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
                'Profil & Penautan Akun',
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
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                auth.fullName ?? auth.username ?? 'Pengguna',
                                style: AppTypography.body(text, size: AppTypography.textSm, weight: FontWeight.w600),
                              ),
                              const SizedBox(height: AppSpacing.space1),
                              Text(
                                auth.email ?? 'Email belum diatur',
                                style: AppTypography.mono(textSec, size: AppTypography.textXs),
                              ),
                            ],
                          ),
                        ),
                        AppBadge(
                          label: auth.role?.toUpperCase() ?? 'MEMBER',
                          variant: AppBadgeVariant.neutral,
                        ),
                      ],
                    ),
                    const Divider(height: AppSpacing.space6),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Akun Google',
                                style: AppTypography.body(text, size: AppTypography.textSm, weight: FontWeight.w600),
                              ),
                              const SizedBox(height: AppSpacing.space1),
                              Text(
                                'Masuk praktis via Google OAuth',
                                style: AppTypography.body(textSec, size: AppTypography.textXs),
                              ),
                            ],
                          ),
                        ),
                        AppBadge(
                          label: auth.isGoogleLinked ? 'TERTAUT' : 'BELUM TERTAUT',
                          variant: auth.isGoogleLinked ? AppBadgeVariant.ok : AppBadgeVariant.neutral,
                        ),
                      ],
                    ),
                    const SizedBox(height: AppSpacing.space4),
                    if (auth.isGoogleLinked)
                      AppButton(
                        label: 'Lepas Tautan Akun Google',
                        variant: AppButtonVariant.secondary,
                        onPressed: _handleUnlinkGoogle,
                        icon: Icon(
                          PhosphorIcons.linkBreak(),
                          size: AppDimensions.iconSizeSm,
                          color: text,
                        ),
                      )
                    else
                      AppButton(
                        label: 'Tautkan Akun Google',
                        variant: AppButtonVariant.secondary,
                        onPressed: _showLinkGoogleModal,
                        icon: Icon(
                          PhosphorIcons.globe(),
                          size: AppDimensions.iconSizeSm,
                          color: text,
                        ),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.space4),
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
