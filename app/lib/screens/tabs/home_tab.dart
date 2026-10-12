import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_badge.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/core/api_client.dart';
import 'package:app/core/auth_state.dart';
import 'package:app/theme/tokens.dart';

class HomeTab extends ConsumerStatefulWidget {
  const HomeTab({super.key});

  @override
  ConsumerState<HomeTab> createState() => _HomeTabState();
}

class _HomeTabState extends ConsumerState<HomeTab> {
  Map<String, dynamic>? _healthData;
  bool _isLoadingHealth = false;

  @override
  void initState() {
    super.initState();
    _fetchHealth();
  }

  Future<void> _fetchHealth() async {
    setState(() => _isLoadingHealth = true);
    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.get('/api/health');
      if (mounted) {
        setState(() {
          _healthData = res.data as Map<String, dynamic>?;
          _isLoadingHealth = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _healthData = null;
          _isLoadingHealth = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final auth = ref.watch(authProvider);

    final roleStr = auth.role ?? 'member';
    AppBadgeVariant roleVariant;
    switch (roleStr) {
      case 'admin':
        roleVariant = AppBadgeVariant.ok;
        break;
      case 'member':
        roleVariant = AppBadgeVariant.neutral;
        break;
      default:
        roleVariant = AppBadgeVariant.warn;
    }

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Icon(
              PhosphorIcons.house(),
              size: AppDimensions.iconSizeSm,
              color: text,
            ),
            const SizedBox(width: AppSpacing.space2),
            const Text('Beranda'),
          ],
        ),
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _fetchHealth,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(AppSpacing.space4),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Halo, ${auth.username ?? "Pengguna"}',
                          style: AppTypography.body(
                            text,
                            size: AppTypography.textLg,
                            weight: FontWeight.w700,
                          ),
                        ),
                        Text(
                          'Sistem Rumah berjalan lokal',
                          style: AppTypography.body(textSec, size: AppTypography.textSm),
                        ),
                      ],
                    ),
                    AppBadge(
                      label: roleStr.toUpperCase(),
                      variant: roleVariant,
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.space4),
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              Icon(
                                PhosphorIcons.cpu(),
                                size: AppDimensions.iconSizeSm,
                                color: text,
                              ),
                              const SizedBox(width: AppSpacing.space2),
                              Text(
                                'Status Backend Server',
                                style: AppTypography.body(
                                  text,
                                  size: AppTypography.textMd,
                                  weight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                          _isLoadingHealth
                              ? const AppBadge(
                                  label: 'MEMERIKSA...',
                                  variant: AppBadgeVariant.warn,
                                )
                              : _healthData != null
                                  ? const AppBadge(
                                      label: 'ONLINE',
                                      variant: AppBadgeVariant.ok,
                                    )
                                  : const AppBadge(
                                      label: 'TERPUTUS',
                                      variant: AppBadgeVariant.danger,
                                    ),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.space3),
                      _buildStatRow('Layanan API', 'FastAPI (Python 3.11)', text, textSec),
                      _buildStatRow(
                        'Database',
                        _healthData != null
                            ? 'SQLite (${_healthData!["database"]?["journal_mode"]?.toString().toUpperCase() ?? "WAL"})'
                            : 'Belum terhubung',
                        text,
                        textSec,
                      ),
                      _buildStatRow(
                        'Uptime',
                        _healthData != null
                            ? '${_healthData!["uptime_seconds"]} detik'
                            : '-',
                        text,
                        textSec,
                      ),
                      const SizedBox(height: AppSpacing.space3),
                      AppButton(
                        label: 'Periksa Ulang',
                        variant: AppButtonVariant.secondary,
                        onPressed: _fetchHealth,
                        icon: Icon(
                          PhosphorIcons.arrowsClockwise(),
                          size: AppDimensions.iconSizeSm,
                          color: text,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.space4),
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Kemajuan Proyek "Rumah"',
                        style: AppTypography.body(
                          text,
                          size: AppTypography.textMd,
                          weight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: AppSpacing.space2),
                      _buildCheckItem('Tahap 0: Fondasi repo & keputusan', true, text),
                      _buildCheckItem('Tahap 1: Backend inti, autentikasi & Flutter', true, text),
                      _buildCheckItem('Tahap 2: Kontrol IoT MQTT & ESP32 firmware', false, textSec),
                      _buildCheckItem('Tahap 3: Asisten suara & DeepSeek LLM', false, textSec),
                      _buildCheckItem('Tahap 4: Kamera HP bekas & WebRTC MediaMTX', false, textSec),
                      _buildCheckItem('Tahap 5: AI Vision & pencarian benda YOLO11', false, textSec),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStatRow(String label, String value, Color text, Color textSec) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.space1),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: AppTypography.body(textSec, size: AppTypography.textSm)),
          Text(
            value,
            style: AppTypography.mono(
              text,
              size: AppTypography.textSm,
              weight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCheckItem(String label, bool isDone, Color text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.space1),
      child: Row(
        children: [
          Icon(
            isDone ? PhosphorIcons.checkCircle() : PhosphorIcons.circle(),
            size: AppDimensions.iconSizeSm,
            color: isDone ? AppColors.statusOk : text,
          ),
          const SizedBox(width: AppSpacing.space2),
          Expanded(
            child: Text(
              label,
              style: AppTypography.body(text, size: AppTypography.textSm),
            ),
          ),
        ],
      ),
    );
  }
}
