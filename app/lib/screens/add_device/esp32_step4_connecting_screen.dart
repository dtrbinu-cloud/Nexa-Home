import 'dart:async';
import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_top_bar.dart';
import 'package:app/screens/add_device/esp32_error_screen.dart';
import 'package:app/screens/add_device/esp32_success_screen.dart';
import 'package:app/theme/tokens.dart';

class Esp32Step4ConnectingScreen extends StatefulWidget {
  final bool simulateError;

  const Esp32Step4ConnectingScreen({super.key, this.simulateError = false});

  @override
  State<Esp32Step4ConnectingScreen> createState() => _Esp32Step4ConnectingScreenState();
}

class _Esp32Step4ConnectingScreenState extends State<Esp32Step4ConnectingScreen> {
  final int _currentStep = 2; // 0, 1, 2 (mengaktifkan), 3 (selesai)
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer(const Duration(seconds: 3), () {
      if (!mounted) return;
      if (widget.simulateError) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const Esp32ErrorScreen(variant: Esp32ErrorVariant.wrongPassword)),
        );
      } else {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const Esp32SuccessScreen()),
        );
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

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
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMargin),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: AppSpacing.space2),

              // Stepper 4 dari 4 (100%)
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Langkah 4 dari 4',
                    style: AppTypography.body(
                      textSec,
                      size: AppTypography.textXs,
                      weight: FontWeight.w500,
                    ),
                  ),
                  Text(
                    '100%',
                    style: AppTypography.mono(
                      accent,
                      size: AppTypography.textXs,
                      weight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.space2),
              Row(
                children: [
                  Expanded(child: Container(height: 4, decoration: BoxDecoration(color: accent, borderRadius: AppRadius.borderBar))),
                  const SizedBox(width: 6),
                  Expanded(child: Container(height: 4, decoration: BoxDecoration(color: accent, borderRadius: AppRadius.borderBar))),
                  const SizedBox(width: 6),
                  Expanded(child: Container(height: 4, decoration: BoxDecoration(color: accent, borderRadius: AppRadius.borderBar))),
                  const SizedBox(width: 6),
                  Expanded(child: Container(height: 4, decoration: BoxDecoration(color: accent, borderRadius: AppRadius.borderBar))),
                ],
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              Text(
                'Menghubungkan',
                style: AppTypography.body(
                  text,
                  size: AppTypography.textLg,
                  weight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: AppSpacing.space2),
              Text(
                'Jangan matikan alat atau tutup aplikasi selama proses berlangsung.',
                style: AppTypography.body(textSec, size: AppTypography.textSm),
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              // Stepper Vertikal
              AppCard(
                padding: const EdgeInsets.all(AppSpacing.space5),
                child: Column(
                  children: [
                    _buildStepRow(
                      title: 'Menyambung ke WiFi rumah',
                      subtitle: 'Tersambung ke Rumah-Utama',
                      isCompleted: _currentStep > 0,
                      isActive: _currentStep == 0,
                      isLast: false,
                      accent: accent,
                      text: text,
                      textSec: textSec,
                      subtle: subtle,
                    ),
                    _buildStepRow(
                      title: 'Menghubungi server',
                      subtitle: 'Server lokal terdeteksi',
                      isCompleted: _currentStep > 1,
                      isActive: _currentStep == 1,
                      isLast: false,
                      accent: accent,
                      text: text,
                      textSec: textSec,
                      subtle: subtle,
                    ),
                    _buildStepRow(
                      title: 'Mengaktifkan perangkat',
                      subtitle: 'Sedang diproses...',
                      isCompleted: _currentStep > 2,
                      isActive: _currentStep == 2,
                      isLast: false,
                      accent: accent,
                      text: text,
                      textSec: textSec,
                      subtle: subtle,
                    ),
                    _buildStepRow(
                      title: 'Selesai',
                      subtitle: 'Menunggu konfigurasi akhir',
                      isCompleted: _currentStep > 3,
                      isActive: _currentStep == 3,
                      isLast: true,
                      accent: accent,
                      text: text,
                      textSec: textSec,
                      subtle: subtle,
                    ),
                  ],
                ),
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              Center(
                child: Text(
                  'Proses biasanya memakan waktu sekitar 30 detik.',
                  style: AppTypography.body(textSec, size: AppTypography.textXs),
                  textAlign: TextAlign.center,
                ),
              ),

              const SizedBox(height: AppSpacing.space4),

              Center(
                child: TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: Text(
                    'Batal',
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

  Widget _buildStepRow({
    required String title,
    required String subtitle,
    required bool isCompleted,
    required bool isActive,
    required bool isLast,
    required Color accent,
    required Color text,
    required Color textSec,
    required Color subtle,
  }) {
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Step Icon / Dot + Connecting line
          Column(
            children: [
              Container(
                width: 24.0,
                height: 24.0,
                decoration: BoxDecoration(
                  color: isCompleted
                      ? AppColors.lightAccentLight
                      : (isActive ? accent : subtle),
                  shape: BoxShape.circle,
                ),
                alignment: Alignment.center,
                child: isCompleted
                    ? PhosphorIcon(
                        PhosphorIcons.check(),
                        size: 14.0,
                        color: accent,
                      )
                    : (isActive
                        ? Container(
                            width: 8.0,
                            height: 8.0,
                            decoration: const BoxDecoration(
                              color: AppColors.lightSurface,
                              shape: BoxShape.circle,
                            ),
                          )
                        : const SizedBox.shrink()),
              ),
              if (!isLast)
                Expanded(
                  child: Container(
                    width: 2.0,
                    color: isCompleted ? accent : subtle,
                  ),
                ),
            ],
          ),
          const SizedBox(width: AppSpacing.space3),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.space5),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: AppTypography.body(
                      text,
                      size: AppTypography.textSm,
                      weight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 2.0),
                  Text(
                    subtitle,
                    style: AppTypography.body(
                      isActive ? accent : textSec,
                      size: AppTypography.textXs,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
