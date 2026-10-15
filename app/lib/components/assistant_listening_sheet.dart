import 'dart:async';
import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:app/components/app_button.dart';
import 'package:app/theme/tokens.dart';

class AssistantListeningSheet extends StatefulWidget {
  final ValueChanged<String> onTranscriptComplete;

  const AssistantListeningSheet({
    super.key,
    required this.onTranscriptComplete,
  });

  @override
  State<AssistantListeningSheet> createState() => _AssistantListeningSheetState();
}

class _AssistantListeningSheetState extends State<AssistantListeningSheet>
    with SingleTickerProviderStateMixin {
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isListening = false;
  String _wordsSpoken = 'Matikan lampu di ruang tengah...';
  double _soundLevel = 0.5;
  Timer? _animTimer;
  late AnimationController _animController;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    )..repeat(reverse: true);

    _initSpeech();
  }

  Future<void> _initSpeech() async {
    try {
      final available = await _speech.initialize(
        onError: (_) {},
        onStatus: (status) {
          if (status == 'notListening' && mounted) {
            setState(() => _isListening = false);
          }
        },
      );

      if (available && mounted) {
        setState(() => _isListening = true);
        await _speech.listen(
          onResult: (result) {
            if (mounted) {
              setState(() {
                _wordsSpoken = result.recognizedWords;
              });
            }
          },
          onSoundLevelChange: (level) {
            if (mounted) {
              setState(() {
                _soundLevel = (level.clamp(0.0, 10.0) / 10.0);
              });
            }
          },
        );
      }
    } catch (_) {
      // Fallback simulasi visualizer jika perangkat tanpa mikrofon
      _animTimer = Timer.periodic(const Duration(milliseconds: 150), (timer) {
        if (mounted) {
          setState(() {
            _soundLevel = 0.2 + (timer.tick % 5) * 0.15;
          });
        }
      });
    }
  }

  void _finish() {
    _speech.stop();
    _animTimer?.cancel();
    Navigator.of(context).pop();
    if (_wordsSpoken.isNotEmpty && _wordsSpoken != 'Matikan lampu di ruang tengah...') {
      widget.onTranscriptComplete(_wordsSpoken);
    }
  }

  @override
  void dispose() {
    _animTimer?.cancel();
    _animController.dispose();
    _speech.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final surface = isDark ? AppColors.darkSurface : AppColors.lightSurface;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;
    final subtle = isDark ? AppColors.darkSubtle : AppColors.lightSubtle;

    return Container(
      decoration: BoxDecoration(
        color: surface,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(AppRadius.card),
          topRight: Radius.circular(AppRadius.card),
        ),
      ),
      padding: const EdgeInsets.symmetric(
        horizontal: AppDimensions.screenMargin,
        vertical: AppSpacing.space4,
      ),
      child: SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Drag handle
            Container(
              width: 36.0,
              height: 4.0,
              decoration: BoxDecoration(
                color: subtle,
                borderRadius: AppRadius.borderBar,
              ),
            ),

            const SizedBox(height: AppSpacing.space6),

            // Mic circle icon
            Container(
              width: 64.0,
              height: 64.0,
              decoration: BoxDecoration(
                color: accent,
                shape: BoxShape.circle,
              ),
              alignment: Alignment.center,
              child: PhosphorIcon(
                PhosphorIcons.microphone(),
                size: AppDimensions.iconSizeLg,
                color: AppColors.lightSurface,
              ),
            ),

            const SizedBox(height: AppSpacing.space4),

            // Title "Mendengarkan" (18/600)
            Text(
              'Mendengarkan',
              style: AppTypography.body(
                text,
                size: AppTypography.textMd,
                weight: FontWeight.w600,
              ),
            ),

            const SizedBox(height: AppSpacing.space4),

            // 4-Bar Sound Wave Indicator Visualizer
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _buildBar(14.0 + _soundLevel * 18.0, accent),
                const SizedBox(width: 4.0),
                _buildBar(22.0 + _soundLevel * 24.0, accent),
                const SizedBox(width: 4.0),
                _buildBar(18.0 + _soundLevel * 20.0, accent),
                const SizedBox(width: 4.0),
                _buildBar(12.0 + _soundLevel * 14.0, accent),
              ],
            ),

            const SizedBox(height: AppSpacing.space5),

            // Transkrip teks
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space4),
              child: Text(
                _wordsSpoken,
                style: AppTypography.body(
                  text,
                  size: AppTypography.textSm,
                  weight: FontWeight.w500,
                ),
                textAlign: TextAlign.center,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ),

            const SizedBox(height: AppSpacing.space2),

            Text(
              _isListening
                  ? 'Bicara sekarang atau tekan tombol untuk selesai.'
                  : 'Mempersiapkan mikrofon...',
              style: AppTypography.body(
                textSec,
                size: AppTypography.textXs,
              ),
              textAlign: TextAlign.center,
            ),

            const SizedBox(height: AppSpacing.space6),

            // Tombol Berhenti (fill inset/subtle)
            AppButton(
              label: 'Berhenti',
              variant: AppButtonVariant.secondary,
              onPressed: _finish,
            ),

            const SizedBox(height: AppSpacing.space3),
          ],
        ),
      ),
    );
  }

  Widget _buildBar(double height, Color color) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 100),
      width: 4.0,
      height: height.clamp(8.0, 40.0),
      decoration: BoxDecoration(
        color: color,
        borderRadius: AppRadius.borderBar,
      ),
    );
  }
}
