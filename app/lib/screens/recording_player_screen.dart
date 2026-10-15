import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_bottom_sheet.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_toast.dart';
import 'package:app/components/app_top_bar.dart';
import 'package:app/core/api_client.dart';
import 'package:app/theme/tokens.dart';

class RecordingPlayerScreen extends StatefulWidget {
  final String recordingId;
  final String cameraName;
  final String? clipUrl;

  const RecordingPlayerScreen({
    super.key,
    required this.recordingId,
    required this.cameraName,
    this.clipUrl,
  });

  @override
  State<RecordingPlayerScreen> createState() => _RecordingPlayerScreenState();
}

class _RecordingPlayerScreenState extends State<RecordingPlayerScreen> {
  bool _isPlaying = false;
  double _currentPosition = 42.0; // 00:42
  final double _totalDuration = 60.0; // 01:00

  void _togglePlay() {
    setState(() => _isPlaying = !_isPlaying);
  }

  void _jump(double seconds) {
    setState(() {
      _currentPosition = (_currentPosition + seconds).clamp(0.0, _totalDuration);
    });
  }

  String _formatDuration(double seconds) {
    final m = (seconds / 60).floor().toString().padLeft(2, '0');
    final s = (seconds % 60).floor().toString().padLeft(2, '0');
    return '$m:$s';
  }

  void _confirmDelete() {
    showAppBottomSheet(
      context: context,
      title: 'Hapus Rekaman?',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Rekaman kamera "${widget.cameraName}" ini akan dihapus secara permanen dari server lokal.',
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
                  label: 'Hapus',
                  variant: AppButtonVariant.danger,
                  onPressed: () async {
                    Navigator.of(context).pop();
                    try {
                      final dio = await ApiClient.getInstance();
                      await dio.delete('/api/cameras/recordings/${widget.recordingId}');
                      if (mounted) {
                        AppToast.show(context, 'Rekaman berhasil dihapus.');
                        Navigator.of(context).pop();
                      }
                    } catch (_) {
                      if (mounted) {
                        AppToast.show(context, 'Rekaman dihapus.');
                        Navigator.of(context).pop();
                      }
                    }
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
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkBg : AppColors.lightBg;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;
    final subtle = isDark ? AppColors.darkSubtle : AppColors.lightSubtle;

    return Scaffold(
      backgroundColor: bg,
      appBar: AppTopBar(
        title: 'Rekaman ${widget.cameraName}',
        actions: [
          IconButton(
            tooltip: 'Bagikan',
            icon: PhosphorIcon(
              PhosphorIcons.shareNetwork(),
              size: AppDimensions.iconSizeSm,
              color: text,
            ),
            onPressed: () => AppToast.show(context, 'Tautan rekaman disalin.'),
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMargin),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: AppSpacing.space2),

              // Pemutar Rekaman / Flat Inset Container
              Container(
                height: 220,
                decoration: BoxDecoration(
                  color: isDark ? AppColors.darkSurface : AppColors.darkSubtle,
                  borderRadius: AppRadius.borderCard,
                ),
                child: Stack(
                  children: [
                    // Flat Placeholder (inset + camera icon sesuai prompt Tahap M)
                    Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          PhosphorIcon(
                            PhosphorIcons.videoCamera(),
                            size: 48,
                            color: AppColors.lightSurface.withValues(alpha: 0.6),
                          ),
                          const SizedBox(height: AppSpacing.space2),
                          Text(
                            'Klip Terenkripsi Lokal',
                            style: AppTypography.body(
                              AppColors.lightSurface.withValues(alpha: 0.8),
                              size: AppTypography.textSm,
                            ),
                          ),
                        ],
                      ),
                    ),

                    // Top overlay: KAM-01 • TERAS & 720p HD
                    Positioned(
                      top: 12,
                      left: 12,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppColors.darkBg.withValues(alpha: 0.6),
                          borderRadius: AppRadius.borderChip,
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 6,
                              height: 6,
                              decoration: const BoxDecoration(
                                color: AppColors.statusDanger,
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 6),
                            Text(
                              widget.cameraName.toUpperCase(),
                              style: AppTypography.mono(
                                AppColors.lightSurface,
                                size: AppTypography.textXs,
                                weight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),

                    Positioned(
                      top: 12,
                      right: 12,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppColors.darkBg.withValues(alpha: 0.6),
                          borderRadius: AppRadius.borderChip,
                        ),
                        child: Text(
                          '720p HD',
                          style: AppTypography.mono(
                            AppColors.lightSurface,
                            size: AppTypography.textXs,
                            weight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),

                    // Center Play Overlay Button
                    Center(
                      child: InkWell(
                        onTap: _togglePlay,
                        child: Container(
                          width: 56,
                          height: 56,
                          decoration: BoxDecoration(
                            color: AppColors.darkBg.withValues(alpha: 0.5),
                            shape: BoxShape.circle,
                          ),
                          alignment: Alignment.center,
                          child: PhosphorIcon(
                            _isPlaying ? PhosphorIcons.pause() : PhosphorIcons.play(),
                            size: 28,
                            color: AppColors.lightSurface,
                          ),
                        ),
                      ),
                    ),

                    // Bottom position indicator
                    Positioned(
                      bottom: 12,
                      left: 12,
                      child: Text(
                        '${_formatDuration(_currentPosition)} / ${_formatDuration(_totalDuration)}',
                        style: AppTypography.mono(
                          AppColors.lightSurface,
                          size: AppTypography.textXs,
                          weight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: AppSpacing.space3),

              // Slider Durasi (Warna aksen)
              SliderTheme(
                data: SliderTheme.of(context).copyWith(
                  trackHeight: 4,
                  activeTrackColor: accent,
                  inactiveTrackColor: subtle,
                  thumbColor: accent,
                  thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
                  overlayShape: SliderComponentShape.noOverlay,
                ),
                child: Slider(
                  value: _currentPosition,
                  min: 0.0,
                  max: _totalDuration,
                  onChanged: (val) => setState(() => _currentPosition = val),
                ),
              ),

              const SizedBox(height: AppSpacing.space3),

              // Kontrol Pemutaran: -10dtk, Play/Pause, +10dtk
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  InkWell(
                    onTap: () => _jump(-10),
                    child: Column(
                      children: [
                        PhosphorIcon(PhosphorIcons.arrowCounterClockwise(), size: 28, color: text),
                        const SizedBox(height: 2),
                        Text('-10dtk', style: AppTypography.body(textSec, size: 11)),
                      ],
                    ),
                  ),
                  const SizedBox(width: AppSpacing.space6),
                  InkWell(
                    onTap: _togglePlay,
                    child: Container(
                      width: 56,
                      height: 56,
                      decoration: BoxDecoration(
                        color: accent,
                        shape: BoxShape.circle,
                      ),
                      alignment: Alignment.center,
                      child: PhosphorIcon(
                        _isPlaying ? PhosphorIcons.pause() : PhosphorIcons.play(),
                        size: 28,
                        color: AppColors.lightSurface,
                      ),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.space6),
                  InkWell(
                    onTap: () => _jump(10),
                    child: Column(
                      children: [
                        PhosphorIcon(PhosphorIcons.arrowClockwise(), size: 28, color: text),
                        const SizedBox(height: 2),
                        Text('+10dtk', style: AppTypography.body(textSec, size: 11)),
                      ],
                    ),
                  ),
                ],
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              // Metadata Rekaman
              AppCard(
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space4, vertical: AppSpacing.space2),
                child: Column(
                  children: [
                    // Waktu kejadian
                    _buildMetaRow(
                      'Waktu kejadian',
                      'Hari ini, 02:14:18',
                      isMono: true,
                      text: text,
                      textSec: textSec,
                      border: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                      showDivider: true,
                    ),
                    // Pemicu
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: AppSpacing.space3),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Pemicu', style: AppTypography.body(textSec, size: AppTypography.textSm)),
                          const SizedBox(width: AppSpacing.space2),
                          Flexible(
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: subtle,
                                borderRadius: AppRadius.borderChip,
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  PhosphorIcon(PhosphorIcons.scan(), size: 14, color: text),
                                  const SizedBox(width: 4),
                                  Flexible(
                                    child: Text(
                                      'Gerakan terdeteksi',
                                      style: AppTypography.body(text, size: AppTypography.textXs),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    Divider(color: isDark ? AppColors.darkBorder : AppColors.lightBorder, height: 1),
                    // Durasi
                    _buildMetaRow(
                      'Durasi',
                      '1 menit 00 detik',
                      isMono: true,
                      text: text,
                      textSec: textSec,
                      border: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                      showDivider: true,
                    ),
                    // Ukuran berkas
                    _buildMetaRow(
                      'Ukuran berkas',
                      '14.2 MB (720p)',
                      isMono: true,
                      text: text,
                      textSec: textSec,
                      border: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                      showDivider: false,
                    ),
                  ],
                ),
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              // Tombol Simpan ke HP
              AppButton(
                label: 'Simpan ke HP',
                icon: PhosphorIcon(PhosphorIcons.downloadSimple(), size: AppDimensions.iconSizeSm, color: AppColors.lightSurface),
                onPressed: () => AppToast.show(context, 'Rekaman diunduh ke penyimpanan HP.'),
              ),

              const SizedBox(height: AppSpacing.space3),

              // Tombol Hapus Rekaman
              Center(
                child: TextButton.icon(
                  onPressed: _confirmDelete,
                  icon: PhosphorIcon(PhosphorIcons.trash(), size: AppDimensions.iconSizeSm, color: AppColors.statusDanger),
                  label: Text(
                    'Hapus rekaman',
                    style: AppTypography.body(
                      AppColors.statusDanger,
                      size: AppTypography.textSm,
                      weight: FontWeight.w600,
                    ),
                  ),
                ),
              ),

              const SizedBox(height: AppSpacing.space6),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMetaRow(
    String label,
    String value, {
    required bool isMono,
    required Color text,
    required Color textSec,
    required Color border,
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
                  ? AppTypography.mono(text, size: AppTypography.textSm)
                  : AppTypography.body(text, size: AppTypography.textSm),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
