import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_bottom_sheet.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/list_row.dart';
import 'package:app/core/auth_state.dart';
import 'package:app/screens/all_devices_screen.dart';
import 'package:app/screens/family_summary_screen.dart';
import 'package:app/screens/notifications_screen.dart';
import 'package:app/screens/settings_screen.dart';
import 'package:app/theme/tokens.dart';

class MoreTab extends ConsumerWidget {
  const MoreTab({super.key});

  void _confirmLogout(BuildContext context, WidgetRef ref) {
    showAppBottomSheet(
      context: context,
      title: 'Keluar dari Akun?',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Anda harus memasukkan kata sandi kembali untuk mengakses sistem rumah ini.',
            style: AppTypography.body(
              Theme.of(context).brightness == Brightness.dark
                  ? AppColors.darkTextSecondary
                  : AppColors.lightTextSecondary,
              size: AppTypography.textSm,
            ),
          ),
          const SizedBox(height: AppSpacing.space6),
          Row(
            children: [
              Expanded(
                child: AppButton(
                  label: 'Batal',
                  variant: AppButtonVariant.secondary,
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ),
              const SizedBox(width: AppSpacing.space3),
              Expanded(
                child: AppButton(
                  label: 'Keluar',
                  variant: AppButtonVariant.danger,
                  onPressed: () {
                    Navigator.of(context).pop();
                    ref.read(authProvider.notifier).logout();
                  },
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkBg : AppColors.lightBg;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final subtle = isDark ? AppColors.darkSubtle : AppColors.lightSubtle;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;

    final auth = ref.watch(authProvider);
    final username = auth.username ?? 'Bapak';
    final role = auth.role ?? 'admin';
    final isAdmin = role.toLowerCase() == 'admin';

    return Scaffold(
      backgroundColor: bg,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMargin),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: AppSpacing.space3),

              // Title 32/600 "Lainnya"
              Text(
                'Lainnya',
                style: AppTypography.body(
                  text,
                  size: AppTypography.textXl, // 32px
                  weight: FontWeight.w600,
                ),
              ),

              const SizedBox(height: AppSpacing.space4),

              // User Profile Header Card
              AppCard(
                padding: const EdgeInsets.all(AppSpacing.space4),
                child: Row(
                  children: [
                    Container(
                      width: 48.0,
                      height: 48.0,
                      decoration: BoxDecoration(
                        color: subtle,
                        shape: BoxShape.circle,
                      ),
                      alignment: Alignment.center,
                      child: PhosphorIcon(
                        PhosphorIcons.user(),
                        size: AppDimensions.iconSizeMd,
                        color: text,
                      ),
                    ),
                    const SizedBox(width: AppSpacing.space3),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            username,
                            style: AppTypography.body(
                              text,
                              size: AppTypography.textMd,
                              weight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 2.0),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 2.0),
                            decoration: BoxDecoration(
                              color: isDark ? AppColors.darkAccentLight : AppColors.lightAccentLight,
                              borderRadius: AppRadius.borderChip,
                            ),
                            child: Text(
                              isAdmin ? 'Admin' : 'Anggota',
                              style: AppTypography.body(
                                accent,
                                size: 11.0,
                                weight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              // List Navigasi Utama
              AppCard(
                padding: EdgeInsets.zero,
                child: Column(
                  children: [
                    // 1. Perangkat -> AllDevicesScreen
                    ListRow(
                      leading: PhosphorIcon(PhosphorIcons.cpu(), size: AppDimensions.iconSizeSm, color: text),
                      title: 'Perangkat',
                      subtitle: 'Semua lampu, saklar, dan sensor',
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => const AllDevicesScreen()),
                        );
                      },
                      showDivider: true,
                    ),

                    // 2. Keluarga (hanya jika role admin)
                    if (isAdmin)
                      ListRow(
                        leading: PhosphorIcon(PhosphorIcons.users(), size: AppDimensions.iconSizeSm, color: text),
                        title: 'Keluarga',
                        subtitle: 'Ringkasan aktivitas dan kehadiran',
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => const FamilySummaryScreen()),
                          );
                        },
                        showDivider: true,
                      ),

                    // 3. Notifikasi -> NotificationsScreen
                    ListRow(
                      leading: PhosphorIcon(PhosphorIcons.bell(), size: AppDimensions.iconSizeSm, color: text),
                      title: 'Notifikasi',
                      subtitle: 'Pusat peringatan dan kejadian rumah',
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => const NotificationsScreen()),
                        );
                      },
                      showDivider: true,
                    ),

                    // 4. Pengaturan -> SettingsScreen
                    ListRow(
                      leading: PhosphorIcon(PhosphorIcons.gear(), size: AppDimensions.iconSizeSm, color: text),
                      title: 'Pengaturan',
                      subtitle: 'Akun, tema, dan preferensi privasi',
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => const SettingsScreen()),
                        );
                      },
                      showDivider: true,
                    ),

                    // 5. Keluar
                    ListRow(
                      leading: PhosphorIcon(PhosphorIcons.signOut(), size: AppDimensions.iconSizeSm, color: AppColors.statusDanger),
                      title: 'Keluar',
                      subtitle: 'Keluar dari akun $username',
                      isDestructive: true,
                      onTap: () => _confirmLogout(context, ref),
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
}
