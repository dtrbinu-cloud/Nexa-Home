import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_input.dart';
import 'package:app/theme/tokens.dart';

class Esp32SuccessScreen extends StatefulWidget {
  const Esp32SuccessScreen({super.key});

  @override
  State<Esp32SuccessScreen> createState() => _Esp32SuccessScreenState();
}

class _Esp32SuccessScreenState extends State<Esp32SuccessScreen> {
  final _nameController = TextEditingController(text: 'Lampu ruang tengah');
  String _selectedRoom = 'Ruang tengah';

  @override
  void dispose() {
    _nameController.dispose();
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
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMargin),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const SizedBox(height: AppSpacing.space8),

              // Circle Success Checkmark
              Container(
                width: 64.0,
                height: 64.0,
                decoration: BoxDecoration(
                  color: isDark ? AppColors.darkAccentLight : AppColors.lightAccentLight,
                  shape: BoxShape.circle,
                ),
                alignment: Alignment.center,
                child: PhosphorIcon(
                  PhosphorIcons.check(),
                  size: 32.0,
                  color: accent,
                ),
              ),

              const SizedBox(height: AppSpacing.space4),

              Text(
                'Perangkat terhubung',
                style: AppTypography.body(
                  text,
                  size: AppTypography.textLg,
                  weight: FontWeight.w600,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: AppSpacing.space2),
              Text(
                'Modul Rumah (ESP32) berhasil dikonfigurasi dan siap digunakan.',
                style: AppTypography.body(textSec, size: AppTypography.textSm),
                textAlign: TextAlign.center,
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              // Form Nama & Ruangan
              AppInput(
                label: 'Nama perangkat',
                controller: _nameController,
              ),

              const SizedBox(height: AppDimensions.cardGap),

              // Ruangan Selector
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Ruangan',
                    style: AppTypography.body(
                      textSec,
                      size: AppTypography.textXs,
                      weight: FontWeight.w600,
                    ),
                  ),
                  InkWell(
                    onTap: () {
                      final rooms = ['Ruang tengah', 'Dapur', 'Kamar', 'Teras'];
                      final next = rooms[(rooms.indexOf(_selectedRoom) + 1) % rooms.length];
                      setState(() => _selectedRoom = next);
                    },
                    borderRadius: AppRadius.borderSm,
                    child: Container(
                      height: AppDimensions.controlHeight,
                      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space4),
                      decoration: BoxDecoration(
                        color: subtle,
                        borderRadius: AppRadius.borderSm,
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            _selectedRoom,
                            style: AppTypography.body(text, size: AppTypography.textSm),
                          ),
                          PhosphorIcon(
                            PhosphorIcons.caretDown(),
                            size: AppDimensions.iconSizeSm,
                            color: textSec,
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: AppDimensions.cardGap),

              // Info ID & IP
              AppCard(
                backgroundColor: subtle,
                padding: const EdgeInsets.all(AppSpacing.space4),
                child: Row(
                  children: [
                    Expanded(
                      child: Row(
                        children: [
                          PhosphorIcon(PhosphorIcons.cpu(), size: 16, color: textSec),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('ID:', style: AppTypography.body(textSec, size: AppTypography.textXs)),
                                Text('esp32-ruang-01', style: AppTypography.mono(text, size: AppTypography.textXs)),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    Container(width: 1, height: 32, color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
                    const SizedBox(width: AppSpacing.space3),
                    Expanded(
                      child: Row(
                        children: [
                          PhosphorIcon(PhosphorIcons.broadcast(), size: 16, color: textSec),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('IP:', style: AppTypography.body(textSec, size: AppTypography.textXs)),
                                Text('192.168.1.42', style: AppTypography.mono(text, size: 11)),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: AppDimensions.sectionGap * 2),

              AppButton(
                label: 'Selesai',
                onPressed: () {
                  Navigator.of(context).popUntil((route) => route.isFirst);
                },
              ),

              const SizedBox(height: AppSpacing.space6),
            ],
          ),
        ),
      ),
    );
  }
}
