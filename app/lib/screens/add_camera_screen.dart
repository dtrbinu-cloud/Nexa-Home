import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_toast.dart';
import 'package:app/components/app_top_bar.dart';
import 'package:app/core/api_client.dart';
import 'package:app/theme/tokens.dart';

class AddCameraScreen extends StatefulWidget {
  const AddCameraScreen({super.key});

  @override
  State<AddCameraScreen> createState() => _AddCameraScreenState();
}

class _AddCameraScreenState extends State<AddCameraScreen> {
  bool _isLoading = true;
  String _pairingCode = '719 304';
  String _expiresAt = '09:48';

  @override
  void initState() {
    super.initState();
    _generateCode();
  }

  Future<void> _generateCode() async {
    setState(() => _isLoading = true);
    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.post('/api/cameras/pairing-codes', data: {
        'camera_name': 'Kamera HP Bekas',
        'room_id': 'default',
      });
      if (res.statusCode == 200 && mounted) {
        final codeRaw = res.data['code']?.toString() ?? '719304';
        final formatted = codeRaw.length == 6
            ? '${codeRaw.substring(0, 3)} ${codeRaw.substring(3)}'
            : codeRaw;

        final expRaw = res.data['expires_at']?.toString() ?? '';
        String expTime = '09:48';
        if (expRaw.contains('T')) {
          final parts = expRaw.split('T')[1].split(':');
          if (parts.length >= 2) expTime = '${parts[0]}:${parts[1]}';
        }

        setState(() {
          _pairingCode = formatted;
          _expiresAt = expTime;
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _copyCode() {
    Clipboard.setData(ClipboardData(text: _pairingCode.replaceAll(' ', '')));
    AppToast.show(context, 'Kode pairing disalin ke papan klip.');
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
      appBar: const AppTopBar(title: 'Tambah Kamera'),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMargin),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: AppSpacing.space3),

              Text(
                'Jadikan HP bekas sebagai kamera',
                style: AppTypography.body(
                  text,
                  size: AppTypography.textLg, // 24px
                  weight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: AppSpacing.space2),
              Text(
                'Buka aplikasi Kamera Rumah di HP bekas, lalu masukkan kode pairing ini:',
                style: AppTypography.body(textSec, size: AppTypography.textSm),
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              // Kartu Kode Pairing
              AppCard(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.space4,
                  vertical: AppSpacing.space6,
                ),
                child: Center(
                  child: Column(
                    children: [
                      Text(
                        'KODE PAIRING KAMERA',
                        style: AppTypography.body(
                          textSec,
                          size: AppTypography.textXs,
                          weight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: AppSpacing.space3),
                      Text(
                        _isLoading ? '--- ---' : _pairingCode,
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
                            _expiresAt,
                            style: AppTypography.mono(textSec, size: AppTypography.textXs),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: AppDimensions.cardGap),

              // Petunjuk Langkah
              AppCard(
                backgroundColor: subtle,
                padding: const EdgeInsets.all(AppSpacing.space4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildInstructionRow('1.', 'Pasang aplikasi Kamera Rumah di HP lama.', text),
                    const SizedBox(height: AppSpacing.space3),
                    _buildInstructionRow('2.', 'Hubungkan HP lama ke WiFi rumah yang sama.', text),
                    const SizedBox(height: AppSpacing.space3),
                    _buildInstructionRow('3.', 'Masukkan kode di atas pada layar HP lama.', text),
                  ],
                ),
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              // Tombol Salin Kode (Secondary, fill subtle)
              AppButton(
                label: 'Salin kode',
                variant: AppButtonVariant.secondary,
                icon: PhosphorIcon(PhosphorIcons.copy(), size: AppDimensions.iconSizeSm, color: text),
                onPressed: _copyCode,
              ),

              const SizedBox(height: AppSpacing.space3),

              Center(
                child: TextButton(
                  onPressed: _generateCode,
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

  Widget _buildInstructionRow(String number, String text, Color textColor) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 20,
          child: Text(
            number,
            style: AppTypography.mono(textColor, size: AppTypography.textSm, weight: FontWeight.w600),
          ),
        ),
        const SizedBox(width: 6),
        Expanded(
          child: Text(
            text,
            style: AppTypography.body(textColor, size: AppTypography.textSm),
          ),
        ),
      ],
    );
  }
}
