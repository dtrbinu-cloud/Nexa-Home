import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_bottom_sheet.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_input.dart';
import 'package:app/components/app_switch.dart';
import 'package:app/components/app_toast.dart';
import 'package:app/components/app_top_bar.dart';
import 'package:app/components/list_row.dart';
import 'package:app/core/api_client.dart';
import 'package:app/core/auth_state.dart';
import 'package:app/screens/manage_members_screen.dart';
import 'package:app/theme/tokens.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  bool _privacyMode = false;
  String _serverVersion = '1.0.0';
  final String _appVersion = '1.0.0+1';

  @override
  void initState() {
    super.initState();
    _fetchServerHealth();
  }

  Future<void> _fetchServerHealth() async {
    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.get('/api/health');
      if (res.statusCode == 200 && mounted) {
        setState(() {
          _serverVersion = res.data['version']?.toString() ?? '1.0.0';
        });
      }
    } catch (_) {}
  }

  void _showChangePasswordSheet() {
    final oldPassCtrl = TextEditingController();
    final newPassCtrl = TextEditingController();

    showAppBottomSheet(
      context: context,
      title: 'Ganti Kata Sandi',
      child: Column(
        children: [
          AppInput(
            label: 'Kata Sandi Lama',
            controller: oldPassCtrl,
            obscureText: true,
          ),
          const SizedBox(height: AppSpacing.space3),
          AppInput(
            label: 'Kata Sandi Baru',
            controller: newPassCtrl,
            obscureText: true,
          ),
          const SizedBox(height: AppDimensions.sectionGap),
          AppButton(
            label: 'Simpan Kata Sandi',
            onPressed: () async {
              Navigator.of(context).pop();
              try {
                final dio = await ApiClient.getInstance();
                await dio.post('/api/auth/change-password', data: {
                  'old_password': oldPassCtrl.text,
                  'new_password': newPassCtrl.text,
                });
                if (mounted) AppToast.show(context, 'Kata sandi berhasil diperbarui.');
              } catch (_) {
                if (mounted) AppToast.show(context, 'Gagal memperbarui kata sandi.', isError: true);
              }
            },
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkBg : AppColors.lightBg;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;
    final subtle = isDark ? AppColors.darkSubtle : AppColors.lightSubtle;

    final themeMode = ref.watch(themeModeProvider);
    final auth = ref.watch(authProvider);
    final isAdmin = (auth.role ?? 'admin').toLowerCase() == 'admin';

    return Scaffold(
      backgroundColor: bg,
      appBar: const AppTopBar(title: 'Pengaturan Sistem'),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMargin),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: AppSpacing.space2),

              // Bagian 1: Akun
              Text(
                'Akun',
                style: AppTypography.body(textSec, size: AppTypography.textXs, weight: FontWeight.w600),
              ),
              const SizedBox(height: AppSpacing.space2),
              AppCard(
                padding: EdgeInsets.zero,
                child: Column(
                  children: [
                    ListRow(
                      leading: PhosphorIcon(PhosphorIcons.lockKey(), size: AppDimensions.iconSizeSm, color: text),
                      title: 'Ganti kata sandi',
                      onTap: _showChangePasswordSheet,
                      showDivider: true,
                    ),
                    ListRow(
                      leading: PhosphorIcon(PhosphorIcons.shieldCheck(), size: AppDimensions.iconSizeSm, color: text),
                      title: 'Autentikasi dua faktor (2FA)',
                      trailing: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: isDark ? AppColors.darkAccentLight : AppColors.lightAccentLight,
                          borderRadius: AppRadius.borderChip,
                        ),
                        child: Text(
                          'Aktif',
                          style: AppTypography.body(accent, size: 11, weight: FontWeight.w600),
                        ),
                      ),
                      showDivider: false,
                    ),
                  ],
                ),
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              // Bagian 2: Tampilan
              Text(
                'Tampilan',
                style: AppTypography.body(textSec, size: AppTypography.textXs, weight: FontWeight.w600),
              ),
              const SizedBox(height: AppSpacing.space2),
              AppCard(
                padding: const EdgeInsets.all(AppSpacing.space4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Tema Aplikasi', style: AppTypography.body(text, size: AppTypography.textSm, weight: FontWeight.w500)),
                    const SizedBox(height: AppSpacing.space3),
                    Container(
                      height: 40,
                      decoration: BoxDecoration(
                        color: subtle,
                        borderRadius: AppRadius.borderSm,
                      ),
                      padding: const EdgeInsets.all(3),
                      child: Row(
                        children: [
                          _buildThemeOption('light', 'Terang', themeMode, accent, text, textSec, isDark),
                          _buildThemeOption('dark', 'Gelap', themeMode, accent, text, textSec, isDark),
                          _buildThemeOption('system', 'Ikuti sistem', themeMode, accent, text, textSec, isDark),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              // Bagian 3: Privasi
              Text(
                'Privasi',
                style: AppTypography.body(textSec, size: AppTypography.textXs, weight: FontWeight.w600),
              ),
              const SizedBox(height: AppSpacing.space2),
              AppCard(
                padding: EdgeInsets.zero,
                child: Column(
                  children: [
                    ListRow(
                      leading: PhosphorIcon(PhosphorIcons.eyeSlash(), size: AppDimensions.iconSizeSm, color: text),
                      title: 'Mode privasi kamera',
                      subtitle: 'Matikan stream kamera dalam ruangan',
                      trailing: AppSwitch(
                        value: _privacyMode,
                        onChanged: (val) {
                          setState(() => _privacyMode = val);
                          AppToast.show(context, val ? 'Semua kamera masuk mode privasi.' : 'Mode privasi dinonaktifkan.');
                        },
                      ),
                      showDivider: true,
                    ),
                    ListRow(
                      leading: PhosphorIcon(PhosphorIcons.clockCounterClockwise(), size: AppDimensions.iconSizeSm, color: text),
                      title: 'Hapus rekaman otomatis setelah',
                      trailing: Text('14 hari', style: AppTypography.mono(text, size: AppTypography.textSm)),
                      showDivider: false,
                    ),
                  ],
                ),
              ),

              if (isAdmin) ...[
                const SizedBox(height: AppDimensions.sectionGap),

                // Bagian 4: Anggota (Hanya Admin)
                Text(
                  'Anggota',
                  style: AppTypography.body(textSec, size: AppTypography.textXs, weight: FontWeight.w600),
                ),
                const SizedBox(height: AppSpacing.space2),
                AppCard(
                  padding: EdgeInsets.zero,
                  child: ListRow(
                    leading: PhosphorIcon(PhosphorIcons.users(), size: AppDimensions.iconSizeSm, color: text),
                    title: 'Kelola anggota keluarga',
                    subtitle: 'Tambah akun dan atur hak akses',
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const ManageMembersScreen()),
                      );
                    },
                    showDivider: false,
                  ),
                ),
              ],

              const SizedBox(height: AppDimensions.sectionGap),

              // Bagian 5: Tentang
              Text(
                'Tentang',
                style: AppTypography.body(textSec, size: AppTypography.textXs, weight: FontWeight.w600),
              ),
              const SizedBox(height: AppSpacing.space2),
              AppCard(
                padding: EdgeInsets.zero,
                child: Column(
                  children: [
                    ListRow(
                      title: 'Versi aplikasi',
                      trailing: Text(_appVersion, style: AppTypography.mono(textSec, size: AppTypography.textSm)),
                      showDivider: true,
                    ),
                    ListRow(
                      title: 'Versi server hub',
                      trailing: Text(_serverVersion, style: AppTypography.mono(textSec, size: AppTypography.textSm)),
                      showDivider: false,
                    ),
                  ],
                ),
              ),

              const SizedBox(height: AppSpacing.space6),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildThemeOption(
    String modeKey,
    String label,
    String currentMode,
    Color accent,
    Color text,
    Color textSec,
    bool isDark,
  ) {
    final isSelected = currentMode == modeKey;
    final activeBg = isDark ? AppColors.darkSurface : AppColors.lightSurface;

    return Expanded(
      child: InkWell(
        onTap: () {
          ref.read(themeModeProvider.notifier).setTheme(modeKey);
        },
        borderRadius: AppRadius.borderChip,
        child: Container(
          decoration: BoxDecoration(
            color: isSelected ? activeBg : AppColors.transparent,
            borderRadius: AppRadius.borderChip,
          ),
          alignment: Alignment.center,
          child: Text(
            label,
            style: AppTypography.body(
              isSelected ? accent : textSec,
              size: AppTypography.textXs,
              weight: isSelected ? FontWeight.w600 : FontWeight.w400,
            ),
          ),
        ),
      ),
    );
  }
}
