import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_badge.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_toast.dart';
import 'package:app/components/app_top_bar.dart';
import 'package:app/components/empty_state.dart';
import 'package:app/core/api_client.dart';
import 'package:app/theme/tokens.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  bool _isLoading = true;
  List<dynamic> _logs = [];
  String _activeFilter = 'Semua';
  final _filters = const ['Semua', 'Penting & Bahaya', 'Kehadiran'];

  @override
  void initState() {
    super.initState();
    _fetchLogs();
  }

  Future<void> _fetchLogs() async {
    setState(() => _isLoading = true);
    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.get('/api/audit/logs?limit=50');
      if (res.statusCode == 200 && mounted) {
        setState(() {
          _logs = res.data['logs'] as List<dynamic>? ?? [];
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkBg : AppColors.lightBg;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;

    return Scaffold(
      backgroundColor: bg,
      appBar: AppTopBar(
        title: 'Pusat Notifikasi',
        actions: [
          TextButton.icon(
            onPressed: () => AppToast.show(context, 'Semua notifikasi ditandai telah dibaca.'),
            icon: PhosphorIcon(PhosphorIcons.check(), size: 14, color: accent),
            label: Text(
              'Tandai dibaca',
              style: AppTypography.body(accent, size: AppTypography.textXs, weight: FontWeight.w600),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: AppSpacing.space2),

            // Filter Chips
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMargin),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: _filters.map((f) {
                    return Padding(
                      padding: const EdgeInsets.only(right: AppSpacing.space2),
                      child: AppChip(
                        label: f,
                        isSelected: _activeFilter == f,
                        onTap: () => setState(() => _activeFilter = f),
                      ),
                    );
                  }).toList(),
                ),
              ),
            ),

            const SizedBox(height: AppSpacing.space4),

            Expanded(
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : _logs.isEmpty
                      ? const Center(
                          child: EmptyState(
                            icon: Icon(Icons.notifications_none, size: 48),
                            title: 'Belum ada notifikasi',
                            description: 'Aktivitas sistem dan deteksi sensor akan muncul di sini.',
                          ),
                        )
                      : RefreshIndicator(
                          onRefresh: _fetchLogs,
                          color: accent,
                          child: ListView(
                            padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMargin),
                            children: [
                              Text(
                                'Hari Ini',
                                style: AppTypography.body(textSec, size: AppTypography.textXs, weight: FontWeight.w600),
                              ),
                              const SizedBox(height: AppSpacing.space2),

                              ..._logs.map((log) {
                                final action = log['action']?.toString() ?? 'Aktivitas sistem';
                                final rawTime = log['timestamp']?.toString() ?? '';
                                final desc = log['description']?.toString() ?? action;

                                final isDanger = action.contains('danger') || action.contains('gas') || action.contains('alert');
                                String timeOnly = '19:44';
                                if (rawTime.contains('T')) {
                                  final parts = rawTime.split('T')[1].split(':');
                                  if (parts.length >= 2) timeOnly = '${parts[0]}:${parts[1]}';
                                }

                                return Padding(
                                  padding: const EdgeInsets.only(bottom: AppDimensions.cardGap),
                                  child: AppCard(
                                    padding: const EdgeInsets.all(AppSpacing.space4),
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            // Status Dot datar 8px
                                            Container(
                                              margin: const EdgeInsets.only(top: 6),
                                              width: 8,
                                              height: 8,
                                              decoration: BoxDecoration(
                                                color: isDanger ? AppColors.statusDanger : AppColors.statusOk,
                                                shape: BoxShape.circle,
                                              ),
                                            ),
                                            const SizedBox(width: AppSpacing.space3),
                                            Expanded(
                                              child: Text(
                                                action,
                                                style: AppTypography.body(
                                                  text,
                                                  size: AppTypography.textSm,
                                                  weight: isDanger ? FontWeight.w600 : FontWeight.w500,
                                                ),
                                              ),
                                            ),
                                            Text(
                                              timeOnly,
                                              style: AppTypography.mono(textSec, size: AppTypography.textXs),
                                            ),
                                          ],
                                        ),
                                        const SizedBox(height: AppSpacing.space2),
                                        Padding(
                                          padding: const EdgeInsets.only(left: 20),
                                          child: Text(
                                            desc,
                                            style: AppTypography.body(textSec, size: AppTypography.textSm),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                );
                              }),

                              const SizedBox(height: AppSpacing.space4),
                              Center(
                                child: TextButton(
                                  onPressed: () => AppToast.show(context, 'Notifikasi lama dibersihkan.'),
                                  child: Text(
                                    'Hapus notifikasi lama',
                                    style: AppTypography.body(textSec, size: AppTypography.textSm),
                                  ),
                                ),
                              ),
                              const SizedBox(height: AppSpacing.space6),
                            ],
                          ),
                        ),
            ),
          ],
        ),
      ),
    );
  }
}
