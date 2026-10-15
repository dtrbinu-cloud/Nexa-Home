import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_top_bar.dart';
import 'package:app/theme/tokens.dart';

enum Esp32ErrorVariant {
  wrongPassword,
  expiredCode,
  serverUnreachable,
}

class Esp32ErrorScreen extends StatelessWidget {
  final Esp32ErrorVariant variant;

  const Esp32ErrorScreen({
    super.key,
    this.variant = Esp32ErrorVariant.wrongPassword,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkBg : AppColors.lightBg;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;

    PhosphorIconData icon;
    String title;
    String description;
    String primaryBtnLabel;

    switch (variant) {
      case Esp32ErrorVariant.wrongPassword:
        icon = PhosphorIcons.wifiSlash();
        title = 'Sandi WiFi salah';
        description = 'Alat tidak dapat terhubung ke jaringan WiFi. Periksa kembali kata sandi WiFi dan coba hubungkan lagi.';
        primaryBtnLabel = 'Coba lagi';
        break;
      case Esp32ErrorVariant.expiredCode:
        icon = PhosphorIcons.clockCountdown();
        title = 'Kode pairing kedaluwarsa';
        description = 'Batas waktu 10 menit kode pairing telah habis. Buat kode pairing baru dan tekan tombol BOOT pada alat.';
        primaryBtnLabel = 'Buat kode baru';
        break;
      case Esp32ErrorVariant.serverUnreachable:
        icon = PhosphorIcons.cloudSlash();
        title = 'Server tidak terjangkau';
        description = 'Modul terhubung ke WiFi tetapi tidak merespons server lokal. Pastikan gateway server rumah menyala dalam subnet yang sama.';
        primaryBtnLabel = 'Cek server';
        break;
    }

    return Scaffold(
      backgroundColor: bg,
      appBar: const AppTopBar(title: 'Gagal Menghubungkan'),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMargin),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const Spacer(flex: 1),

              // Danger Circle Icon
              Container(
                width: 64.0,
                height: 64.0,
                decoration: BoxDecoration(
                  color: AppColors.statusDanger.withValues(alpha: 0.15),
                  shape: BoxShape.circle,
                ),
                alignment: Alignment.center,
                child: PhosphorIcon(
                  icon,
                  size: 32.0,
                  color: AppColors.statusDanger,
                ),
              ),

              const SizedBox(height: AppSpacing.space4),

              Text(
                title,
                style: AppTypography.body(
                  text,
                  size: AppTypography.textLg,
                  weight: FontWeight.w600,
                ),
                textAlign: TextAlign.center,
              ),

              const SizedBox(height: AppSpacing.space3),

              Text(
                description,
                style: AppTypography.body(
                  textSec,
                  size: AppTypography.textSm,
                ),
                textAlign: TextAlign.center,
              ),

              const Spacer(flex: 2),

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
                      label: primaryBtnLabel,
                      variant: AppButtonVariant.primary,
                      onPressed: () => Navigator.of(context).pop(),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: AppSpacing.space3),

              Center(
                child: TextButton(
                  onPressed: () => Navigator.of(context).popUntil((r) => r.isFirst),
                  child: Text(
                    'Kembali ke Beranda',
                    style: AppTypography.body(
                      accent,
                      size: AppTypography.textSm,
                      weight: FontWeight.w600,
                    ),
                  ),
                ),
              ),

              const SizedBox(height: AppSpacing.space4),
            ],
          ),
        ),
      ),
    );
  }
}
