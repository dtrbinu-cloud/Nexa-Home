import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_badge.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/empty_state.dart';
import 'package:app/core/api_client.dart';
import 'package:app/core/auth_state.dart';
import 'package:app/theme/tokens.dart';

class FamilyTab extends ConsumerStatefulWidget {
  const FamilyTab({super.key});

  @override
  ConsumerState<FamilyTab> createState() => _FamilyTabState();
}

class _FamilyTabState extends ConsumerState<FamilyTab> {
  List<dynamic> _auditLogs = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _fetchAuditLogs();
  }

  Future<void> _fetchAuditLogs() async {
    final role = ref.read(authProvider).role;
    if (role != 'admin') return;

    setState(() => _isLoading = true);
    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.get('/api/audit-logs?limit=5');
      if (mounted) {
        setState(() {
          _auditLogs = res.data['logs'] as List? ?? [];
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
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final auth = ref.watch(authProvider);

    final isAdmin = auth.role == 'admin';

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Icon(
              PhosphorIcons.users(),
              size: AppDimensions.iconSizeSm,
              color: text,
            ),
            const SizedBox(width: AppSpacing.space2),
            const Text('Keluarga'),
          ],
        ),
      ),
      body: SafeArea(
        child: !isAdmin
            ? EmptyState(
                icon: Icon(
                  PhosphorIcons.lockKey(),
                  size: AppDimensions.iconSizeMd * 2,
                  color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                ),
                title: 'Akses Dibatasi',
                description:
                    'Fitur pengawasan keluarga hanya dapat diakses oleh akun orang tua (admin).',
              )
            : SingleChildScrollView(
                padding: const EdgeInsets.all(AppSpacing.space4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AppCard(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                'Pengawasan & Log Audit',
                                style: AppTypography.body(
                                  text,
                                  size: AppTypography.textMd,
                                  weight: FontWeight.w600,
                                ),
                              ),
                              const AppBadge(
                                label: 'ADMIN ONLY',
                                variant: AppBadgeVariant.ok,
                              ),
                            ],
                          ),
                          const SizedBox(height: AppSpacing.space2),
                          Text(
                            'Catatan kejadian keamanan dan aktivitas sistem tercatat secara transparan.',
                            style: AppTypography.body(textSec, size: AppTypography.textSm),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: AppSpacing.space4),
                    Text(
                      'Aktivitas Terbaru',
                      style: AppTypography.body(
                        text,
                        size: AppTypography.textMd,
                        weight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.space2),
                    if (_isLoading)
                      const Center(child: CircularProgressIndicator())
                    else if (_auditLogs.isEmpty)
                      AppCard(
                        child: Text(
                          'Belum ada log audit yang tercatat.',
                          style: AppTypography.body(textSec, size: AppTypography.textSm),
                        ),
                      )
                    else
                      ..._auditLogs.map((log) {
                        return Padding(
                          padding: const EdgeInsets.only(bottom: AppSpacing.space2),
                          child: AppCard(
                            padding: const EdgeInsets.all(AppSpacing.space3),
                            child: Row(
                              children: [
                                Icon(
                                  PhosphorIcons.notebook(),
                                  size: AppDimensions.iconSizeSm,
                                  color: isDark ? AppColors.darkAccent : AppColors.lightAccent,
                                ),
                                const SizedBox(width: AppSpacing.space3),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        log['action']?.toString() ?? '-',
                                        style: AppTypography.mono(
                                          text,
                                          size: AppTypography.textSm,
                                          weight: FontWeight.w500,
                                        ),
                                      ),
                                      Text(
                                        'Oleh: ${log["username"] ?? "Sistem"} | IP: ${log["ip_address"] ?? "-"}',
                                        style: AppTypography.body(textSec, size: AppTypography.textXs),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      }),
                  ],
                ),
              ),
      ),
    );
  }
}
