import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_badge.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_input.dart';
import 'package:app/components/app_switch.dart';
import 'package:app/components/app_toast.dart';
import 'package:app/components/empty_state.dart';
import 'package:app/theme/tokens.dart';

class DesignScreen extends StatefulWidget {
  const DesignScreen({super.key});

  @override
  State<DesignScreen> createState() => _DesignScreenState();
}

class _DesignScreenState extends State<DesignScreen> {
  bool _switchVal = true;
  final _inputController = TextEditingController(text: 'Teks contoh input');

  @override
  void dispose() {
    _inputController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Katalog Desain & Token'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.space4),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildSectionHeader('1. Token Warna (Tema Aktif)', text),
              Wrap(
                spacing: AppSpacing.space2,
                runSpacing: AppSpacing.space2,
                children: [
                  _buildColorChip('Background', isDark ? AppColors.darkBg : AppColors.lightBg),
                  _buildColorChip('Surface', isDark ? AppColors.darkSurface : AppColors.lightSurface),
                  _buildColorChip('Border', isDark ? AppColors.darkBorder : AppColors.lightBorder),
                  _buildColorChip('Accent', isDark ? AppColors.darkAccent : AppColors.lightAccent),
                  _buildColorChip('Status OK', AppColors.statusOk),
                  _buildColorChip('Status Warn', AppColors.statusWarn),
                  _buildColorChip('Status Danger', AppColors.statusDanger),
                ],
              ),
              const SizedBox(height: AppSpacing.space6),
              _buildSectionHeader('2. Tipografi (Public Sans & IBM Plex Mono)', text),
              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Teks Body (Public Sans - 24px Bold)',
                      style: AppTypography.body(text, size: AppTypography.textLg, weight: FontWeight.w700),
                    ),
                    const SizedBox(height: AppSpacing.space1),
                    Text(
                      'Teks Pendukung (Public Sans - 15px Regular)',
                      style: AppTypography.body(textSec, size: AppTypography.textSm),
                    ),
                    const SizedBox(height: AppSpacing.space2),
                    Text(
                      'LOG_TELEMETRY: MQ2_RAW=1420 LDR=2100 (IBM Plex Mono)',
                      style: AppTypography.mono(text, size: AppTypography.textSm, weight: FontWeight.w500),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.space6),
              _buildSectionHeader('3. Variasi Tombol (AppButton)', text),
              AppButton(
                label: 'Tombol Utama (Primary)',
                onPressed: () => AppToast.show(context, 'Tombol utama ditekan.'),
              ),
              const SizedBox(height: AppSpacing.space2),
              AppButton(
                label: 'Tombol Sekunder (Secondary)',
                variant: AppButtonVariant.secondary,
                onPressed: () => AppToast.show(context, 'Tombol sekunder ditekan.'),
              ),
              const SizedBox(height: AppSpacing.space2),
              AppButton(
                label: 'Tombol Bahaya (Danger)',
                variant: AppButtonVariant.danger,
                onPressed: () => AppToast.show(context, 'Aksi bahaya.', isError: true),
              ),
              const SizedBox(height: AppSpacing.space2),
              const AppButton(
                label: 'Sedang Memuat',
                isLoading: true,
                onPressed: null,
              ),
              const SizedBox(height: AppSpacing.space6),
              _buildSectionHeader('4. Status Badge (AppBadge)', text),
              const Wrap(
                spacing: AppSpacing.space2,
                runSpacing: AppSpacing.space2,
                children: [
                  AppBadge(label: 'ONLINE', variant: AppBadgeVariant.ok),
                  AppBadge(label: 'PERINGATAN', variant: AppBadgeVariant.warn),
                  AppBadge(label: 'BAHAYA', variant: AppBadgeVariant.danger),
                  AppBadge(label: 'NETRAL', variant: AppBadgeVariant.neutral),
                ],
              ),
              const SizedBox(height: AppSpacing.space6),
              _buildSectionHeader('5. Input Teks & Switch', text),
              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AppInput(
                      label: 'Kolom Input Standar',
                      controller: _inputController,
                    ),
                    const SizedBox(height: AppSpacing.space4),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Saklar Toggle Datar (AppSwitch)',
                          style: AppTypography.body(text, size: AppTypography.textSm),
                        ),
                        AppSwitch(
                          value: _switchVal,
                          onChanged: (v) => setState(() => _switchVal = v),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.space6),
              _buildSectionHeader('6. Keadaan Kosong (EmptyState)', text),
              AppCard(
                child: EmptyState(
                  icon: Icon(
                    PhosphorIcons.folderSimple(),
                    size: AppDimensions.iconSizeMd * 2,
                    color: textSec,
                  ),
                  title: 'Komponen EmptyState',
                  description: 'Digunakan seragam saat data belum tersedia atau fitur belum aktif.',
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title, Color text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.space2),
      child: Text(
        title,
        style: AppTypography.body(
          text,
          size: AppTypography.textMd,
          weight: FontWeight.w600,
        ),
      ),
    );
  }

  Widget _buildColorChip(String name, Color color) {
    return Container(
      width: 140,
      padding: const EdgeInsets.all(AppSpacing.space2),
      decoration: BoxDecoration(
        color: color,
        borderRadius: AppRadius.borderSm,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            name,
            style: AppTypography.body(
              color.computeLuminance() > 0.5 ? AppColors.lightText : AppColors.darkText,
              size: AppTypography.textXs,
              weight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
