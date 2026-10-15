import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_top_bar.dart';
import 'package:app/screens/add_device/esp32_qr_scan_screen.dart';
import 'package:app/screens/add_device/esp32_step3_wifi_setup_screen.dart';
import 'package:app/theme/tokens.dart';

class Esp32Step2ConnectWifiScreen extends StatefulWidget {
  const Esp32Step2ConnectWifiScreen({super.key});

  @override
  State<Esp32Step2ConnectWifiScreen> createState() => _Esp32Step2ConnectWifiScreenState();
}

class _Esp32Step2ConnectWifiScreenState extends State<Esp32Step2ConnectWifiScreen> {
  bool _showManual = true;

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

              // Stepper 2 dari 4
              Text(
                'Langkah 2 dari 4',
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
                  Expanded(child: Container(height: 4, decoration: BoxDecoration(color: accent, borderRadius: AppRadius.borderBar))),
                  const SizedBox(width: 6),
                  Expanded(child: Container(height: 4, decoration: BoxDecoration(color: subtle, borderRadius: AppRadius.borderBar))),
                  const SizedBox(width: 6),
                  Expanded(child: Container(height: 4, decoration: BoxDecoration(color: subtle, borderRadius: AppRadius.borderBar))),
                ],
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              Text(
                'Sambung ke WiFi alat',
                style: AppTypography.body(
                  text,
                  size: AppTypography.textLg,
                  weight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: AppSpacing.space2),
              Text(
                'Scan QR di stiker alat. HP akan tersambung ke WiFi alat.',
                style: AppTypography.body(textSec, size: AppTypography.textSm),
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              // Tombol Scan QR
              AppButton(
                label: 'Scan QR',
                icon: PhosphorIcon(PhosphorIcons.qrCode(), size: AppDimensions.iconSizeSm, color: AppColors.lightSurface),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const Esp32QrScanScreen()),
                  );
                },
              ),

              const SizedBox(height: AppSpacing.space3),

              // Tombol Isi Manual
              AppButton(
                label: 'Isi manual',
                variant: AppButtonVariant.secondary,
                onPressed: () {
                  setState(() => _showManual = !_showManual);
                },
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              if (_showManual)
                AppCard(
                  backgroundColor: subtle,
                  padding: const EdgeInsets.all(AppSpacing.space4),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Detail koneksi manual',
                        style: AppTypography.body(
                          textSec,
                          size: AppTypography.textXs,
                          weight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: AppSpacing.space3),

                      // Nama WiFi
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Nama WiFi', style: AppTypography.body(textSec, size: AppTypography.textXs)),
                              const SizedBox(height: 2),
                              Text('Rumah-A3F9', style: AppTypography.mono(text, size: AppTypography.textSm, weight: FontWeight.w600)),
                            ],
                          ),
                          IconButton(
                            icon: PhosphorIcon(PhosphorIcons.copy(), size: AppDimensions.iconSizeSm, color: textSec),
                            onPressed: () {},
                          ),
                        ],
                      ),

                      const SizedBox(height: AppSpacing.space2),

                      // Sandi
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Sandi', style: AppTypography.body(textSec, size: AppTypography.textXs)),
                              const SizedBox(height: 2),
                              Text('k7Qm-92xT', style: AppTypography.mono(text, size: AppTypography.textSm, weight: FontWeight.w600)),
                            ],
                          ),
                          IconButton(
                            icon: PhosphorIcon(PhosphorIcons.copy(), size: AppDimensions.iconSizeSm, color: textSec),
                            onPressed: () {},
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

              const Spacer(),

              Center(
                child: Text(
                  'Pastikan lampu indikator pada alat berkedip perlahan.',
                  style: AppTypography.body(textSec, size: AppTypography.textXs),
                  textAlign: TextAlign.center,
                ),
              ),

              const SizedBox(height: AppSpacing.space4),

              // Tombol lanjut ke step 3
              AppButton(
                label: 'Lanjut ke Setup WiFi',
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const Esp32Step3WifiSetupScreen()),
                  );
                },
              ),

              const SizedBox(height: AppSpacing.space4),
            ],
          ),
        ),
      ),
    );
  }
}
