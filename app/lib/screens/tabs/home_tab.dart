import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_badge.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/danger_banner.dart';
import 'package:app/components/device_tile.dart';
import 'package:app/core/api_client.dart';
import 'package:app/screens/add_device/choose_type_screen.dart';
import 'package:app/screens/all_devices_screen.dart';
import 'package:app/screens/device_detail_screen.dart';
import 'package:app/screens/notifications_screen.dart';
import 'package:app/theme/tokens.dart';

class HomeTab extends ConsumerStatefulWidget {
  final bool forceDanger; // Untuk keperluan testing / golden preview Layar 4

  const HomeTab({super.key, this.forceDanger = false});

  @override
  ConsumerState<HomeTab> createState() => _HomeTabState();
}

class _HomeTabState extends ConsumerState<HomeTab> {
  bool _isLoading = true;
  List<dynamic> _devices = [];
  List<dynamic> _recentEvents = [];
  String _selectedRoom = 'Semua';
  Timer? _refreshTimer;

  int _gasValue = 412;
  final int _gasThreshold = 1500;
  bool _isGasAlert = false;
  String _gasRoom = 'Dapur';
  String _lightStatus = 'Terang';
  int _onlineCount = 0;
  int _totalDevices = 0;

  @override
  void initState() {
    super.initState();
    if (widget.forceDanger) {
      _isGasAlert = true;
      _gasValue = 1820;
    }
    _loadData();
    _refreshTimer = Timer.periodic(const Duration(seconds: 5), (_) => _loadData(silent: true));
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadData({bool silent = false}) async {
    if (!silent) setState(() => _isLoading = true);

    try {
      final dio = await ApiClient.getInstance();
      
      // Ambil data devices
      final devRes = await dio.get('/api/devices');
      if (devRes.statusCode == 200 && mounted) {
        final list = devRes.data['devices'] as List<dynamic>? ?? [];
        _devices = list;
        _totalDevices = list.length;
        _onlineCount = list.where((d) => d['is_online'] == true).length;

        // Cari data sensor gas dan cahaya
        for (final d in list) {
          final channels = d['channels'] as List<dynamic>? ?? [];
          for (final c in channels) {
            final type = c['channel_type']?.toString();
            final key = c['channel_key']?.toString();
            final val = c['current_value'];

            if (type == 'gas_sensor' || key == 'mq2') {
              if (val != null) {
                final parsed = int.tryParse(val.toString()) ?? (double.tryParse(val.toString())?.toInt() ?? 412);
                if (!widget.forceDanger) {
                  _gasValue = parsed;
                  _isGasAlert = _gasValue >= _gasThreshold;
                }
                _gasRoom = d['room']?.toString() ?? 'Dapur';
              }
            } else if (type == 'light_sensor' || key == 'ldr') {
              if (val != null) {
                final isBright = val.toString().toLowerCase() == 'true' || val.toString() == '1' || val.toString() == 'terang';
                _lightStatus = isBright ? 'Terang' : 'Gelap';
              }
            }
          }
        }
      }

      // Ambil events terbaru
      try {
        final auditRes = await dio.get('/api/audit/logs', queryParameters: {'limit': 5});
        if (auditRes.statusCode == 200 && mounted) {
          final logs = auditRes.data['logs'] as List<dynamic>? ?? [];
          _recentEvents = logs;
        }
      } catch (_) {}

      if (mounted) {
        setState(() => _isLoading = false);
      }
    } catch (_) {
      if (mounted && !silent) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _toggleDevice(Map<String, dynamic> device, Map<String, dynamic> channel) async {
    final devId = device['id'] as String;
    final chKey = channel['channel_key'] as String;
    final currentStr = channel['current_value']?.toString() ?? 'false';
    final currentBool = currentStr.toLowerCase() == 'true' || currentStr == '1';
    final nextVal = !currentBool;

    // Optimistic UI update
    setState(() {
      channel['current_value'] = nextVal.toString();
    });

    try {
      final dio = await ApiClient.getInstance();
      await dio.post('/api/devices/$devId/cmd', data: {
        'channel': chKey,
        'action': 'set',
        'value': nextVal,
      });
    } catch (_) {
      // Revert if error
      if (mounted) {
        setState(() {
          channel['current_value'] = currentBool.toString();
        });
      }
    }
  }

  Future<void> _triggerAlarm(bool turnOn) async {
    try {
      final dio = await ApiClient.getInstance();
      for (final d in _devices) {
        final channels = d['channels'] as List<dynamic>? ?? [];
        for (final c in channels) {
          if (c['channel_type'] == 'buzzer' || c['channel_key'] == 'buzzer') {
            await dio.post('/api/devices/${d['id']}/cmd', data: {
              'channel': c['channel_key'],
              'action': 'set',
              'value': turnOn,
            });
          }
        }
      }
    } catch (_) {}
  }

  PhosphorIconData _resolveIcon(String type, String key) {
    if (type == 'switch' || key.contains('lamp')) {
      return PhosphorIcons.lightbulb();
    }
    if (type == 'relay' || key.contains('fan')) {
      return PhosphorIcons.fan();
    }
    if (type == 'buzzer' || key.contains('alarm')) {
      return PhosphorIcons.bellRinging();
    }
    if (type == 'gas_sensor') {
      return PhosphorIcons.gauge();
    }
    return PhosphorIcons.cpu();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkBg : AppColors.lightBg;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final subtle = isDark ? AppColors.darkSubtle : AppColors.lightSubtle;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;

    // Kumpulkan rooms
    final rooms = <String>{'Semua'};
    for (final d in _devices) {
      if (d['room'] != null && d['room'].toString().isNotEmpty) {
        rooms.add(d['room'].toString());
      }
    }

    // Filter perangkat yang ditampilkan di grid
    final gridItems = <Map<String, dynamic>>[];
    for (final d in _devices) {
      final room = d['room']?.toString() ?? 'Umum';
      if (_selectedRoom != 'Semua' && room != _selectedRoom) continue;

      final channels = d['channels'] as List<dynamic>? ?? [];
      for (final c in channels) {
        final type = c['channel_type']?.toString();
        if (type == 'switch' || type == 'relay' || type == 'buzzer') {
          gridItems.add({
            'device': d,
            'channel': c,
          });
        }
      }
    }

    final now = DateTime.now();
    final timeStr = "${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}";

    return Scaffold(
      backgroundColor: bg,
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () => _loadData(),
          color: isDark ? AppColors.darkAccent : AppColors.lightAccent,
          backgroundColor: isDark ? AppColors.darkSurface : AppColors.lightSurface,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMargin),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: AppSpacing.space3),

                // Top Bar Beranda: Title 32/600 + Actions (Bell & Plus)
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Expanded(
                      child: Text(
                        'Beranda',
                        style: AppTypography.body(
                          text,
                          size: AppTypography.textXl, // 32px
                          weight: FontWeight.w600,
                        ),
                      ),
                    ),
                    Row(
                      children: [
                        IconButton(
                          tooltip: 'Notifikasi',
                          icon: PhosphorIcon(
                            PhosphorIcons.bell(),
                            size: AppDimensions.iconSizeMd,
                            color: text,
                          ),
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(builder: (_) => const NotificationsScreen()),
                            );
                          },
                        ),
                        const SizedBox(width: AppSpacing.space1),
                        InkWell(
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(builder: (_) => const ChooseDeviceTypeScreen()),
                            );
                          },
                          borderRadius: const BorderRadius.all(Radius.circular(AppRadius.tile)),
                          child: Container(
                            width: 40.0,
                            height: 40.0,
                            decoration: BoxDecoration(
                              color: subtle,
                              shape: BoxShape.circle,
                            ),
                            alignment: Alignment.center,
                            child: PhosphorIcon(
                              PhosphorIcons.plus(),
                              size: AppDimensions.iconSizeSm,
                              color: text,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),

                const SizedBox(height: AppSpacing.space4),

                // Banner Bahaya (Layar 4) bila kondisi gas >= threshold atau forceDanger
                if (_isGasAlert) ...[
                  DangerBanner(
                    title: 'Gas terdeteksi di $_gasRoom',
                    currentValue: _gasValue,
                    threshold: _gasThreshold,
                    onTriggerAlarm: () => _triggerAlarm(true),
                    onMuteAlarm: () => _triggerAlarm(false),
                  ),
                  const SizedBox(height: AppSpacing.space3),
                ],

                // Kartu Ringkasan Status
                AppCard(
                  padding: const EdgeInsets.all(AppSpacing.space4),
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Flexible(
                            child: AppStatusDot(
                              label: _isGasAlert ? 'Bahaya terdeteksi' : 'Semua aman',
                              variant: _isGasAlert ? AppBadgeVariant.danger : AppBadgeVariant.ok,
                              isBold: true,
                            ),
                          ),
                          const SizedBox(width: AppSpacing.space2),
                          Text(
                            timeStr,
                            style: AppTypography.mono(
                              textSec,
                              size: AppTypography.textXs,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.space4),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          // Kolom Gas (angka mentah mono tanpa satuan)
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Gas',
                                  style: AppTypography.body(textSec, size: AppTypography.textXs),
                                ),
                                const SizedBox(height: 2.0),
                                Text(
                                  _isGasAlert ? 'Bahaya' : 'Aman',
                                  style: AppTypography.body(
                                    _isGasAlert ? AppColors.statusDanger : AppColors.statusOk,
                                    size: AppTypography.textSm,
                                    weight: FontWeight.w600,
                                  ),
                                ),
                                const SizedBox(height: 2.0),
                                Text(
                                  '$_gasValue',
                                  style: AppTypography.mono(
                                    textSec,
                                    size: AppTypography.textXs,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          // Kolom Cahaya (hanya Terang / Gelap)
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Cahaya',
                                  style: AppTypography.body(textSec, size: AppTypography.textXs),
                                ),
                                const SizedBox(height: 2.0),
                                Text(
                                  _lightStatus,
                                  style: AppTypography.body(
                                    text,
                                    size: AppTypography.textSm,
                                    weight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          // Kolom Online (angka mono)
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Online',
                                  style: AppTypography.body(textSec, size: AppTypography.textXs),
                                ),
                                const SizedBox(height: 2.0),
                                Text(
                                  '$_onlineCount dari $_totalDevices',
                                  style: AppTypography.mono(
                                    text,
                                    size: AppTypography.textSm,
                                    weight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: AppSpacing.space4),

                // Baris Filter Chips Ruangan (horizontal scrollable)
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: rooms.map((r) {
                      final isSelected = _selectedRoom == r;
                      return Padding(
                        padding: const EdgeInsets.only(right: AppSpacing.space2),
                        child: AppChip(
                          label: r,
                          isSelected: isSelected,
                          onTap: () => setState(() => _selectedRoom = r),
                        ),
                      );
                    }).toList(),
                  ),
                ),

                const SizedBox(height: AppDimensions.sectionGap), // 24px

                // Bagian Ruangan (Perangkat Aktif)
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Flexible(
                      child: Text(
                        'Ruangan',
                        style: AppTypography.body(
                          textSec,
                          size: AppTypography.textXs,
                          weight: FontWeight.w600,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(width: AppSpacing.space2),
                    InkWell(
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => const AllDevicesScreen()),
                        );
                      },
                      child: Text(
                        'Semua perangkat',
                        style: AppTypography.body(
                          accent,
                          size: AppTypography.textXs,
                          weight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: AppSpacing.space3),

                if (_isLoading && _devices.isEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: AppSpacing.space6),
                    child: Center(child: CircularProgressIndicator(color: accent, strokeWidth: 2.0)),
                  )
                else if (gridItems.isEmpty)
                  AppCard(
                    padding: const EdgeInsets.all(AppSpacing.space4),
                    child: Center(
                      child: Text(
                        _devices.isEmpty
                            ? 'Belum ada perangkat terhubung.'
                            : 'Tidak ada perangkat di ruangan ini.',
                        style: AppTypography.body(textSec, size: AppTypography.textSm),
                      ),
                    ),
                  )
                else
                  GridView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      mainAxisSpacing: AppDimensions.cardGap, // 12px
                      crossAxisSpacing: AppDimensions.cardGap, // 12px
                      childAspectRatio: 1.15,
                    ),
                    itemCount: gridItems.length,
                    itemBuilder: (context, index) {
                      final item = gridItems[index];
                      final dev = item['device'] as Map<String, dynamic>;
                      final ch = item['channel'] as Map<String, dynamic>;

                      final devName = ch['name']?.toString() ?? dev['name']?.toString() ?? 'Perangkat';
                      final room = dev['room']?.toString() ?? 'Umum';
                      final isOnline = dev['is_online'] == true;
                      final valStr = ch['current_value']?.toString() ?? 'false';
                      final isOn = valStr.toLowerCase() == 'true' || valStr == '1';

                      final iconData = _resolveIcon(
                        ch['channel_type']?.toString() ?? '',
                        ch['channel_key']?.toString() ?? '',
                      );

                      final subtitle = !isOnline
                          ? '$room • Offline'
                          : (isOn ? '$room • Menyala' : '$room • Mati');

                      return DeviceTile(
                        name: devName,
                        subtitle: subtitle,
                        isOn: isOn,
                        isOnline: isOnline,
                        icon: iconData,
                        onToggle: isOnline ? (_) => _toggleDevice(dev, ch) : null,
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => DeviceDetailScreen(deviceId: dev['id'].toString()),
                            ),
                          );
                        },
                      );
                    },
                  ),

                const SizedBox(height: AppDimensions.sectionGap), // 24px

                // Bagian Terakhir (Recent Activity)
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Flexible(
                      child: Text(
                        'Terakhir',
                        style: AppTypography.body(
                          textSec,
                          size: AppTypography.textXs,
                          weight: FontWeight.w600,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(width: AppSpacing.space2),
                    InkWell(
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => const NotificationsScreen()),
                        );
                      },
                      child: Text(
                        'Lihat semua',
                        style: AppTypography.body(
                          isDark ? AppColors.darkAccent : AppColors.lightAccent,
                          size: AppTypography.textXs,
                          weight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: AppSpacing.space3),

                AppCard(
                  padding: EdgeInsets.zero,
                  child: _recentEvents.isEmpty
                      ? Padding(
                          padding: const EdgeInsets.all(AppSpacing.space4),
                          child: Center(
                            child: Text(
                              'Belum ada aktivitas tercatat.',
                              style: AppTypography.body(textSec, size: AppTypography.textSm),
                            ),
                          ),
                        )
                      : Column(
                          children: _recentEvents.asMap().entries.map((entry) {
                            final idx = entry.key;
                            final ev = entry.value;
                            final isLast = idx == _recentEvents.length - 1;

                            final rawTime = ev['timestamp']?.toString() ?? ev['created_at']?.toString() ?? '';
                            String timeOnly = '--:--';
                            if (rawTime.contains('T')) {
                              final parts = rawTime.split('T')[1].split(':');
                              if (parts.length >= 2) timeOnly = '${parts[0]}:${parts[1]}';
                            }

                            final desc = ev['description']?.toString() ?? ev['action']?.toString() ?? 'Aktivitas sistem';

                            return Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: AppSpacing.space4,
                                vertical: AppSpacing.space3,
                              ),
                              decoration: !isLast
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
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    timeOnly,
                                    style: AppTypography.mono(
                                      textSec,
                                      size: AppTypography.textXs,
                                    ),
                                  ),
                                  const SizedBox(width: AppSpacing.space3),
                                  Expanded(
                                    child: Text(
                                      desc,
                                      style: AppTypography.body(
                                        text,
                                        size: AppTypography.textSm,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            );
                          }).toList(),
                        ),
                ),

                const SizedBox(height: AppSpacing.space6),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
