import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/empty_state.dart';
import 'package:app/theme/tokens.dart';

class CamerasTab extends StatelessWidget {
  const CamerasTab({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final text = isDark ? AppColors.darkText : AppColors.lightText;

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Icon(
              PhosphorIcons.videoCamera(),
              size: AppDimensions.iconSizeSm,
              color: text,
            ),
            const SizedBox(width: AppSpacing.space2),
            const Text('Kamera'),
          ],
        ),
      ),
      body: SafeArea(
        child: EmptyState(
          icon: Icon(
            PhosphorIcons.broadcast(),
            size: AppDimensions.iconSizeMd * 2,
            color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
          ),
          title: 'Kamera HP Bekas',
          description:
              'Streaming video lokal via WebRTC/MediaMTX dengan motion trigger dan enkripsi lokal akan diaktifkan di Tahap 4.',
        ),
      ),
    );
  }
}
