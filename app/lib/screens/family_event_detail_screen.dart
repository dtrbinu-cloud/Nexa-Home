import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_top_bar.dart';
import 'package:app/screens/recording_player_screen.dart';
import 'package:app/theme/tokens.dart';

class FamilyEventDetailScreen extends StatelessWidget {
  final Map<String, dynamic> event;

  const FamilyEventDetailScreen({super.key, required this.event});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkBg : AppColors.lightBg;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final subtle = isDark ? AppColors.darkSubtle : AppColors.lightSubtle;

    final eventId = event['id']?.toString() ?? 'EV-8842';
    final title = event['title']?.toString() ?? 'Gerakan di Teras';
    final rawTime = event['created_at']?.toString() ?? '2026-10-14T08:42:15';
    final cameraName = event['camera_name']?.toString() ?? event['camera_id']?.toString() ?? 'Teras Depan';
    final eventType = event['event_type']?.toString() ?? 'Gerakan';

    String timeOnly = '08:42:15';
    if (rawTime.contains('T')) {
      timeOnly = rawTime.split('T')[1].split('.')[0];
    }

    return Scaffold(
      backgroundColor: bg,
      appBar: const AppTopBar(title: 'Detail Kejadian'),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMargin),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: AppSpacing.space3),

              // Title and Event ID
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    width: 44.0,
                    height: 44.0,
                    decoration: BoxDecoration(
                      color: subtle,
                      shape: BoxShape.circle,
                    ),
                    alignment: Alignment.center,
                    child: PhosphorIcon(
                      PhosphorIcons.pulse(),
                      size: AppDimensions.iconSizeSm,
                      color: text,
                    ),
                  ),
                  Text(
                    'ID #$eventId',
                    style: AppTypography.mono(
                      textSec,
                      size: AppTypography.textXs,
                      weight: FontWeight.w600,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: AppSpacing.space3),

              Text(
                title,
                style: AppTypography.body(
                  text,
                  size: AppTypography.textLg, // 24px
                  weight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 2.0),
              Text(
                'Hari ini, $timeOnly WIB',
                style: AppTypography.mono(
                  textSec,
                  size: AppTypography.textXs,
                ),
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              Text(
                'Informasi Kejadian',
                style: AppTypography.body(
                  textSec,
                  size: AppTypography.textXs,
                  weight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: AppSpacing.space3),

              // Kartu Informasi Faktual
              Container(
                decoration: BoxDecoration(
                  color: isDark ? AppColors.darkSurface : AppColors.lightSurface,
                  borderRadius: AppRadius.borderCard,
                ),
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space4, vertical: AppSpacing.space2),
                child: Column(
                  children: [
                    _buildRow('Lokasi', cameraName, text: text, textSec: textSec, border: isDark ? AppColors.darkBorder : AppColors.lightBorder, isMono: false, showDivider: true),
                    _buildRow('Jenis Kejadian', eventType, text: text, textSec: textSec, border: isDark ? AppColors.darkBorder : AppColors.lightBorder, isMono: false, showDivider: true),
                    _buildRow('Waktu', timeOnly, text: text, textSec: textSec, border: isDark ? AppColors.darkBorder : AppColors.lightBorder, isMono: true, showDivider: true),
                    _buildRow('Durasi', '15 detik', text: text, textSec: textSec, border: isDark ? AppColors.darkBorder : AppColors.lightBorder, isMono: true, showDivider: false),
                  ],
                ),
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              Text(
                'Tangkapan Kamera Terkait',
                style: AppTypography.body(
                  textSec,
                  size: AppTypography.textXs,
                  weight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: AppSpacing.space3),

              // Placeholder Tangkapan Kamera Datar (inset + icon)
              Container(
                height: 180,
                decoration: BoxDecoration(
                  color: subtle,
                  borderRadius: AppRadius.borderCard,
                ),
                child: Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      PhosphorIcon(
                        PhosphorIcons.videoCamera(),
                        size: 40,
                        color: textSec,
                      ),
                      const SizedBox(height: AppSpacing.space2),
                      Text(
                        'Klip 15 detik tersedia',
                        style: AppTypography.body(textSec, size: AppTypography.textXs),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              // Tombol Lihat Rekaman Kamera
              AppButton(
                label: 'Lihat Rekaman Kamera',
                icon: PhosphorIcon(PhosphorIcons.videoCamera(), size: AppDimensions.iconSizeSm, color: AppColors.lightSurface),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => RecordingPlayerScreen(
                        recordingId: eventId,
                        cameraName: cameraName,
                      ),
                    ),
                  );
                },
              ),

              const SizedBox(height: AppSpacing.space6),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRow(
    String label,
    String value, {
    required Color text,
    required Color textSec,
    required Color border,
    required bool isMono,
    required bool showDivider,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.space3),
      decoration: showDivider
          ? BoxDecoration(
              border: Border(
                bottom: BorderSide(color: border, width: AppDimensions.borderWidth),
              ),
            )
          : null,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: AppTypography.body(textSec, size: AppTypography.textSm)),
          const SizedBox(width: AppSpacing.space2),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.end,
              style: isMono
                  ? AppTypography.mono(text, size: AppTypography.textSm, weight: FontWeight.w500)
                  : AppTypography.body(text, size: AppTypography.textSm, weight: FontWeight.w500),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
