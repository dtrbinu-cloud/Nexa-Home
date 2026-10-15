import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_button.dart';
import 'package:app/screens/add_device/esp32_step3_wifi_setup_screen.dart';
import 'package:app/theme/tokens.dart';

class Esp32QrScanScreen extends StatefulWidget {
  const Esp32QrScanScreen({super.key});

  @override
  State<Esp32QrScanScreen> createState() => _Esp32QrScanScreenState();
}

class _Esp32QrScanScreenState extends State<Esp32QrScanScreen> {
  bool _flashOn = false;

  @override
  Widget build(BuildContext context) {
    const bgDark = AppColors.darkBg;
    const textLight = AppColors.darkText;
    const textSec = AppColors.darkTextSecondary;
    const accent = AppColors.darkAccent;

    return Scaffold(
      backgroundColor: bgDark,
      body: SafeArea(
        child: Column(
          children: [
            // Top Bar
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: AppDimensions.screenMargin,
                vertical: AppSpacing.space2,
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  IconButton(
                    icon: PhosphorIcon(PhosphorIcons.x(), size: AppDimensions.iconSizeMd, color: textLight),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                  Text(
                    'Scan QR',
                    style: AppTypography.body(
                      textLight,
                      size: AppTypography.textMd,
                      weight: FontWeight.w600,
                    ),
                  ),
                  IconButton(
                    icon: PhosphorIcon(
                      _flashOn ? PhosphorIcons.flashlight(PhosphorIconsStyle.fill) : PhosphorIcons.flashlight(),
                      size: AppDimensions.iconSizeMd,
                      color: textLight,
                    ),
                    onPressed: () => setState(() => _flashOn = !_flashOn),
                  ),
                ],
              ),
            ),

            const Spacer(),

            // Viewfinder Target Square
            Center(
              child: GestureDetector(
                onTap: () {
                  // Simulasi scan berhasil -> navigasi ke Setup WiFi
                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(builder: (_) => const Esp32Step3WifiSetupScreen()),
                  );
                },
                child: Container(
                  width: 240,
                  height: 240,
                  decoration: BoxDecoration(
                    color: AppColors.lightSurface.withValues(alpha: 0.1),
                    borderRadius: AppRadius.borderCard,
                  ),
                  child: Stack(
                    children: [
                      // Sudut kiri atas
                      Positioned(
                        top: 0,
                        left: 0,
                        child: Container(
                          width: 32,
                          height: 32,
                          decoration: const BoxDecoration(
                            border: Border(
                              top: BorderSide(color: accent, width: 3),
                              left: BorderSide(color: accent, width: 3),
                            ),
                            borderRadius: BorderRadius.only(topLeft: Radius.circular(AppRadius.sm)),
                          ),
                        ),
                      ),
                      // Sudut kanan atas
                      Positioned(
                        top: 0,
                        right: 0,
                        child: Container(
                          width: 32,
                          height: 32,
                          decoration: const BoxDecoration(
                            border: Border(
                              top: BorderSide(color: accent, width: 3),
                              right: BorderSide(color: accent, width: 3),
                            ),
                            borderRadius: BorderRadius.only(topRight: Radius.circular(AppRadius.sm)),
                          ),
                        ),
                      ),
                      // Sudut kiri bawah
                      Positioned(
                        bottom: 0,
                        left: 0,
                        child: Container(
                          width: 32,
                          height: 32,
                          decoration: const BoxDecoration(
                            border: Border(
                              bottom: BorderSide(color: accent, width: 3),
                              left: BorderSide(color: accent, width: 3),
                            ),
                            borderRadius: BorderRadius.only(bottomLeft: Radius.circular(AppRadius.sm)),
                          ),
                        ),
                      ),
                      // Sudut kanan bawah
                      Positioned(
                        bottom: 0,
                        right: 0,
                        child: Container(
                          width: 32,
                          height: 32,
                          decoration: const BoxDecoration(
                            border: Border(
                              bottom: BorderSide(color: accent, width: 3),
                              right: BorderSide(color: accent, width: 3),
                            ),
                            borderRadius: BorderRadius.only(bottomRight: Radius.circular(AppRadius.sm)),
                          ),
                        ),
                      ),
                      // Titik tengah
                      const Center(
                        child: CircleAvatar(
                          radius: 4,
                          backgroundColor: accent,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),

            const SizedBox(height: AppDimensions.sectionGap),

            // Petunjuk teks (Public Sans, tanpa SENSOR: AKTIF)
            Text(
              'Arahkan kamera ke QR di stiker alat',
              style: AppTypography.body(
                textLight,
                size: AppTypography.textSm,
                weight: FontWeight.w600,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppSpacing.space1),
            Text(
              'Pastikan kode berada di dalam kotak bidik',
              style: AppTypography.body(
                textSec,
                size: AppTypography.textXs,
              ),
              textAlign: TextAlign.center,
            ),

            const Spacer(),

            // Tombol Batal
            Padding(
              padding: const EdgeInsets.all(AppDimensions.screenMargin),
              child: AppButton(
                label: 'Batal',
                variant: AppButtonVariant.secondary,
                onPressed: () => Navigator.of(context).pop(),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
