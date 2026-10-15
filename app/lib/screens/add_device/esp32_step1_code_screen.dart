import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_top_bar.dart';
import 'package:app/screens/add_device/esp32_step2_connect_wifi_screen.dart';
import 'package:app/theme/tokens.dart';

class Esp32Step1CodeScreen extends StatefulWidget {
  const Esp32Step1CodeScreen({super.key});

  @override
  State<Esp32Step1CodeScreen> createState() => _Esp32Step1CodeScreenState();
}

class _Esp32Step1CodeScreenState extends State<Esp32Step1CodeScreen> {
  final String _code = '482 915';

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkBg : AppColors.lightBg;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;
    final subtle = isDark ? AppColors.darkSubtle : AppColors.lightSubtle;

    return Scaffold(
      backgroundColor: bg,
      appBar: const AppTopBar(title: 'Tambah perangkat'),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMargin),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: AppSpacing.space2),

              // Stepper 1 dari 4
              Text(
                'Langkah 1 dari 4',
                style: AppTypography.body(
                  textSec,
                  size: AppTypography.textXs,
                  weight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: AppSpacing.space2),
              Row(
                children: [
                  Expanded(child: Container(height: 4, decoration: BoxDecoration(color: accent, borderRadius: AppRadius.borderBar))),
                  const SizedBox(width: 6),
                  Expanded(child: Container(height: 4, decoration: BoxDecoration(color: subtle, borderRadius: AppRadius.borderBar))),
                  const SizedBox(width: 6),
                  Expanded(child: Container(height: 4, decoration: BoxDecoration(color: subtle, borderRadius: AppRadius.borderBar))),
                  const SizedBox(width: 6),
                  Expanded(child: Container(height: 4, decoration: BoxDecoration(color: subtle, borderRadius: AppRadius.borderBar))),
                ],
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              Text(
                'Kode pairing',
                style: AppTypography.body(
                  text,
                  size: AppTypography.textLg,
                  weight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: AppSpacing.space2),
              Text(
                'Nyalakan alat. Tahan tombol BOOT 3 detik sampai LED berkedip.',
                style: AppTypography.body(textSec, size: AppTypography.textSm),
              ),

              const Spacer(flex: 1),

              // Kode Pairing Display
              Center(
                child: Column(
                  children: [
                    Text(
                      'KODE PAIRING',
                      style: AppTypography.body(
                        textSec,
                        size: AppTypography.textXs,
                        weight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.space3),
                    Text(
                      _code,
                      style: AppTypography.mono(
                        text,
                        size: AppTypography.textXl, // 32px
                        weight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.space3),
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        PhosphorIcon(
                          PhosphorIcons.clock(),
                          size: AppDimensions.iconSizeSm,
                          color: textSec,
                        ),
                        const SizedBox(width: AppSpacing.space2),
                        Text(
                          'Berlaku ',
                          style: AppTypography.body(textSec, size: AppTypography.textXs),
                        ),
                        Text(
                          '09:42',
                          style: AppTypography.mono(textSec, size: AppTypography.textXs),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              const Spacer(flex: 1),

              // Card Informasi LED
              AppCard(
                backgroundColor: subtle,
                padding: const EdgeInsets.all(AppSpacing.space4),
                child: Row(
                  children: [
                    PhosphorIcon(
                      PhosphorIcons.checkCircle(),
                      size: AppDimensions.iconSizeMd,
                      color: accent,
                    ),
                    const SizedBox(width: AppSpacing.space3),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'LED Berkedip Kuning',
                            style: AppTypography.body(
                              text,
                              size: AppTypography.textSm,
                              weight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            'Perangkat siap menerima sambungan',
                            style: AppTypography.body(
                              textSec,
                              size: AppTypography.textXs,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              // Tombol Lanjut
              AppButton(
                label: 'Lanjut',
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const Esp32Step2ConnectWifiScreen()),
                  );
                },
              ),
              const SizedBox(height: AppSpacing.space3),
              Center(
                child: TextButton(
                  onPressed: () {},
                  child: Text(
                    'Buat kode baru',
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
