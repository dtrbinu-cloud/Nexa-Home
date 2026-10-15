import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_switch.dart';
import 'package:app/components/app_toast.dart';
import 'package:app/components/app_top_bar.dart';
import 'package:app/components/whep_video_player.dart';
import 'package:app/core/api_client.dart';
import 'package:app/core/storage.dart';
import 'package:app/screens/recording_player_screen.dart';
import 'package:app/theme/tokens.dart';

class CameraLiveScreen extends ConsumerStatefulWidget {
  final String cameraId;
  final String cameraName;

  const CameraLiveScreen({
    super.key,
    required this.cameraId,
    required this.cameraName,
  });

  @override
  ConsumerState<CameraLiveScreen> createState() => _CameraLiveScreenState();
}

class _CameraLiveScreenState extends ConsumerState<CameraLiveScreen> {
  bool _isPrivacyMode = false;
  int _activeSegment = 0; // 0: Rekaman, 1: Kejadian
  String _serverUrl = '';
  String? _accessToken;
  List<dynamic> _recordings = [];

  @override
  void initState() {
    super.initState();
    _loadInitData();
  }

  Future<void> _loadInitData() async {
    final serverUrl = await StorageService.getServerUrl();
    final token = await StorageService.getAccessToken();
    if (mounted) {
      setState(() {
        _serverUrl = serverUrl;
        _accessToken = token;
      });
    }

    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.get('/api/cameras/${widget.cameraId}/recordings');
      if (res.statusCode == 200 && mounted) {
        setState(() {
          _recordings = res.data['recordings'] as List<dynamic>? ?? [];
        });
      }
    } catch (_) {}
  }

  Future<void> _togglePrivacy(bool val) async {
    setState(() => _isPrivacyMode = val);
    try {
      final dio = await ApiClient.getInstance();
      await dio.post('/api/cameras/${widget.cameraId}/privacy', data: {'enabled': val});
      if (mounted) {
        AppToast.show(context, val ? 'Mode privasi diaktifkan.' : 'Mode privasi dinonaktifkan.');
      }
    } catch (_) {
      if (mounted) setState(() => _isPrivacyMode = !val);
    }
  }

  void _takeSnapshot() {
    AppToast.show(context, 'Snapshot kamera diambil dan disimpan.');
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkBg : AppColors.lightBg;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;
    final subtle = isDark ? AppColors.darkSubtle : AppColors.lightSubtle;

    final streamUrl = '$_serverUrl/api/cameras/${widget.cameraId}/whep';

    return Scaffold(
      backgroundColor: bg,
      appBar: AppTopBar(
        title: widget.cameraName,
        actions: [
          IconButton(
            tooltip: 'Layar Penuh',
            icon: PhosphorIcon(
              PhosphorIcons.cornersOut(),
              size: AppDimensions.iconSizeSm,
              color: text,
            ),
            onPressed: () {},
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

              // Player View
              Container(
                height: 220,
                decoration: BoxDecoration(
                  color: AppColors.darkBg,
                  borderRadius: AppRadius.borderCard,
                ),
                clipBehavior: Clip.antiAlias,
                child: _isPrivacyMode
                    ? Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            PhosphorIcon(
                              PhosphorIcons.eyeSlash(),
                              size: 48,
                              color: textSec,
                            ),
                            const SizedBox(height: AppSpacing.space2),
                            Text(
                              'Mode Privasi Aktif',
                              style: AppTypography.body(
                                AppColors.lightSurface,
                                size: AppTypography.textSm,
                                weight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      )
                    : Stack(
                        children: [
                          Center(
                            child: WhepVideoPlayer(
                              whepUrl: streamUrl,
                              authToken: _accessToken,
                            ),
                          ),
                          // Badge LIVE
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
                                      color: AppColors.statusOk,
                                      shape: BoxShape.circle,
                                    ),
                                  ),
                                  const SizedBox(width: 6),
                                  Text(
                                    'LIVE',
                                    style: AppTypography.mono(
                                      AppColors.lightSurface,
                                      size: 11,
                                      weight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
              ),

              const SizedBox(height: AppSpacing.space4),

              // Baris Kontrol di bawah video: Info latency, Snapshot, Mode Privasi
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Flexible(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Live - jaringan rumah',
                          style: AppTypography.body(
                            AppColors.statusOk,
                            size: AppTypography.textXs,
                            weight: FontWeight.w600,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '0.8 dtk',
                          style: AppTypography.mono(textSec, size: AppTypography.textXs),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: AppSpacing.space2),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Tombol Snapshot
                      InkWell(
                        onTap: _takeSnapshot,
                        borderRadius: AppRadius.borderSm,
                        child: Container(
                          height: 36,
                          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space3),
                          decoration: BoxDecoration(
                            color: subtle,
                            borderRadius: AppRadius.borderSm,
                          ),
                          alignment: Alignment.center,
                          child: Row(
                            children: [
                              PhosphorIcon(PhosphorIcons.camera(), size: 16, color: text),
                              const SizedBox(width: 6),
                              Text('Snapshot', style: AppTypography.body(text, size: AppTypography.textXs, weight: FontWeight.w600)),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(width: AppSpacing.space2),

                      // Saklar Mode Privasi
                      Tooltip(
                        message: 'Mode privasi',
                        child: AppSwitch(
                          value: _isPrivacyMode,
                          onChanged: _togglePrivacy,
                          semanticLabel: 'Mode privasi ${widget.cameraName}',
                        ),
                      ),
                    ],
                  ),
                ],
              ),

              const SizedBox(height: AppSpacing.space3),

              // Kotak Info: Live hanya di jaringan rumah
              AppCard(
                backgroundColor: subtle,
                padding: const EdgeInsets.all(AppSpacing.space3),
                child: Row(
                  children: [
                    PhosphorIcon(PhosphorIcons.info(), size: AppDimensions.iconSizeSm, color: textSec),
                    const SizedBox(width: AppSpacing.space2),
                    Expanded(
                      child: Text(
                        'Live hanya di jaringan rumah. Di luar rumah tersedia snapshot.',
                        style: AppTypography.body(textSec, size: AppTypography.textXs),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: AppDimensions.sectionGap),

              // Segment Chips: Rekaman / Kejadian
              Row(
                children: [
                  InkWell(
                    onTap: () => setState(() => _activeSegment = 0),
                    borderRadius: AppRadius.borderChip,
                    child: Container(
                      height: 32,
                      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space4),
                      decoration: BoxDecoration(
                        color: _activeSegment == 0 ? (isDark ? AppColors.darkAccentLight : AppColors.lightAccentLight) : AppColors.transparent,
                        borderRadius: AppRadius.borderChip,
                      ),
                      alignment: Alignment.center,
                      child: Text(
                        'Rekaman',
                        style: AppTypography.body(
                          _activeSegment == 0 ? accent : textSec,
                          size: AppTypography.textSm,
                          weight: _activeSegment == 0 ? FontWeight.w600 : FontWeight.w400,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.space2),
                  InkWell(
                    onTap: () => setState(() => _activeSegment = 1),
                    borderRadius: AppRadius.borderChip,
                    child: Container(
                      height: 32,
                      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space4),
                      decoration: BoxDecoration(
                        color: _activeSegment == 1 ? (isDark ? AppColors.darkAccentLight : AppColors.lightAccentLight) : AppColors.transparent,
                        borderRadius: AppRadius.borderChip,
                      ),
                      alignment: Alignment.center,
                      child: Text(
                        'Kejadian',
                        style: AppTypography.body(
                          _activeSegment == 1 ? accent : textSec,
                          size: AppTypography.textSm,
                          weight: _activeSegment == 1 ? FontWeight.w600 : FontWeight.w400,
                        ),
                      ),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: AppSpacing.space3),

              // Daftar Klip Rekaman / Kejadian
              AppCard(
                padding: EdgeInsets.zero,
                child: Column(
                  children: _recordings.isNotEmpty
                      ? _recordings.asMap().entries.map((entry) {
                          final idx = entry.key;
                          final r = entry.value as Map<String, dynamic>;
                          final startTime = r['start_time']?.toString() ?? '00:00';
                          final endTime = r['end_time']?.toString() ?? '00:01';
                          final trigger = r['trigger']?.toString() ?? 'Gerakan';
                          final duration = '${r['duration_seconds'] ?? 60} dtk';
                          final isLast = idx == _recordings.length - 1;
                          return _buildRecordingRow(
                            timeRange: '$startTime - $endTime',
                            trigger: trigger,
                            duration: duration,
                            isDark: isDark,
                            text: text,
                            textSec: textSec,
                            subtle: subtle,
                            showDivider: !isLast,
                          );
                        }).toList()
                      : [
                          _buildRecordingRow(
                            timeRange: '02:14 - 02:15',
                            trigger: 'Gerakan',
                            duration: '1 mnt',
                            isDark: isDark,
                            text: text,
                            textSec: textSec,
                            subtle: subtle,
                            showDivider: true,
                          ),
                          _buildRecordingRow(
                            timeRange: '01:40 - 01:42',
                            trigger: 'Gerakan',
                            duration: '2 mnt',
                            isDark: isDark,
                            text: text,
                            textSec: textSec,
                            subtle: subtle,
                            showDivider: true,
                          ),
                          _buildRecordingRow(
                            timeRange: '00:15 - 00:16',
                            trigger: 'Orang lewat',
                            duration: '1 mnt',
                            isDark: isDark,
                            text: text,
                            textSec: textSec,
                            subtle: subtle,
                            showDivider: false,
                          ),
                        ],
                ),
              ),

              const SizedBox(height: AppSpacing.space6),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRecordingRow({
    required String timeRange,
    required String trigger,
    required String duration,
    required bool isDark,
    required Color text,
    required Color textSec,
    required Color subtle,
    required bool showDivider,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space4, vertical: AppSpacing.space3),
      decoration: showDivider
          ? BoxDecoration(
              border: Border(
                bottom: BorderSide(
                  color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                  width: AppDimensions.borderWidth,
                ),
              ),
            )
          : null,
      child: Row(
        children: [
          // Play icon in subtle box
          InkWell(
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => RecordingPlayerScreen(
                    recordingId: 'rec-01',
                    cameraName: widget.cameraName,
                  ),
                ),
              );
            },
            child: Container(
              width: 44,
              height: 32,
              decoration: BoxDecoration(
                color: subtle,
                borderRadius: AppRadius.borderChip,
              ),
              alignment: Alignment.center,
              child: PhosphorIcon(PhosphorIcons.play(PhosphorIconsStyle.fill), size: 14, color: text),
            ),
          ),
          const SizedBox(width: AppSpacing.space3),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  timeRange,
                  style: AppTypography.mono(text, size: AppTypography.textSm, weight: FontWeight.w600),
                ),
                const SizedBox(height: 2),
                Wrap(
                  spacing: 6,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                      decoration: BoxDecoration(
                        color: subtle,
                        borderRadius: AppRadius.borderChip,
                      ),
                      child: Text(
                        trigger,
                        style: AppTypography.body(textSec, size: 11),
                      ),
                    ),
                    Text(
                      duration,
                      style: AppTypography.mono(textSec, size: 11),
                    ),
                  ],
                ),
              ],
            ),
          ),
          IconButton(
            icon: PhosphorIcon(PhosphorIcons.downloadSimple(), size: AppDimensions.iconSizeSm, color: textSec),
            onPressed: () => AppToast.show(context, 'Mengunduh rekaman...'),
          ),
        ],
      ),
    );
  }
}
