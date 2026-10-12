import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_badge.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_switch.dart';
import 'package:app/components/app_toast.dart';
import 'package:app/components/empty_state.dart';
import 'package:app/core/api_client.dart';
import 'package:app/core/auth_state.dart';
import 'package:app/screens/add_device_screen.dart';
import 'package:app/theme/tokens.dart';

class DevicesTab extends ConsumerStatefulWidget {
  const DevicesTab({super.key});

  @override
  ConsumerState<DevicesTab> createState() => _DevicesTabState();
}

class _DevicesTabState extends ConsumerState<DevicesTab> {
  bool _isLoading = true;
  List<dynamic> _devices = [];
  Timer? _refreshTimer;

  // Cache riwayat telemetri untuk sparkline mini per device
  final Map<String, List<double>> _telemetryHistory = {};

  @override
  void initState() {
    super.initState();
    _fetchDevices();
    _refreshTimer = Timer.periodic(const Duration(seconds: 4), (_) => _fetchDevices(silent: true));
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _fetchDevices({bool silent = false}) async {
    if (!silent) setState(() => _isLoading = true);

    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.get('/api/devices');
      if (res.statusCode == 200 && mounted) {
        final list = res.data['devices'] as List<dynamic>? ?? [];
        setState(() {
          _devices = list;
          _isLoading = false;
        });

        // Update riwayat telemetri untuk tiap sensor
        for (final d in list) {
          final devId = d['id'] as String;
          _fetchSensorHistory(devId);
        }
      }
    } catch (_) {
      if (mounted && !silent) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _fetchSensorHistory(String deviceId) async {
    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.get('/api/devices/$deviceId/telemetry', queryParameters: {'limit': 10});
      if (res.statusCode == 200 && mounted) {
        final logs = res.data['telemetry'] as List<dynamic>? ?? [];
        final vals = logs.map((l) => (l['value'] as num).toDouble()).toList();
        setState(() {
          _telemetryHistory[deviceId] = vals;
        });
      }
    } catch (_) {}
  }

  Future<void> _toggleChannel(String deviceId, String channelKey, bool currentVal) async {
    final newVal = !currentVal;

    // Optimistic update
    setState(() {
      for (final d in _devices) {
        if (d['id'] == deviceId) {
          final channels = d['channels'] as List<dynamic>? ?? [];
          for (final c in channels) {
            if (c['channel_key'] == channelKey) {
              c['current_value'] = newVal.toString();
            }
          }
        }
      }
    });

    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.post(
        '/api/devices/$deviceId/cmd',
        data: {
          'channel': channelKey,
          'action': 'set',
          'value': newVal,
        },
      );
      if (res.statusCode != 200) {
        _fetchDevices(silent: true);
      }
    } catch (e) {
      if (mounted) {
        AppToast.show(context, 'Gagal mengirim perintah kontrol.');
        _fetchDevices(silent: true);
      }
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
            Icon(PhosphorIcons.cpu(), size: AppDimensions.iconSizeSm, color: text),
            const SizedBox(width: AppSpacing.space2),
            const Text('Perangkat'),
          ],
        ),
        actions: [
          if (isAdmin)
            IconButton(
              icon: Icon(PhosphorIcons.plus(), size: AppDimensions.iconSizeSm, color: text),
              tooltip: 'Tambah Perangkat',
              onPressed: () async {
                final created = await Navigator.of(context).push<bool>(
                  MaterialPageRoute(builder: (_) => const AddDeviceScreen()),
                );
                if (created == true) _fetchDevices();
              },
            ),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          color: isDark ? AppColors.darkAccent : AppColors.lightAccent,
          backgroundColor: isDark ? AppColors.darkSurface : AppColors.lightSurface,
          onRefresh: () => _fetchDevices(),
          child: _isLoading && _devices.isEmpty
              ? const Center(child: CircularProgressIndicator())
              : _devices.isEmpty
                  ? _buildEmptyState(isAdmin, isDark)
                  : ListView.separated(
                      padding: const EdgeInsets.all(AppSpacing.space4),
                      itemCount: _devices.length,
                      separatorBuilder: (ctx, i) => const SizedBox(height: AppSpacing.space4),
                      itemBuilder: (context, index) {
                        final dev = _devices[index] as Map<String, dynamic>;
                        return _buildDeviceCard(dev, text, textSec, isDark);
                      },
                    ),
        ),
      ),
    );
  }

  Widget _buildEmptyState(bool isAdmin, bool isDark) {
    return ListView(
      children: [
        SizedBox(height: MediaQuery.of(context).size.height * 0.15),
        EmptyState(
          icon: Icon(
            PhosphorIcons.plugsConnected(),
            size: AppDimensions.iconSizeMd * 2,
            color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
          ),
          title: 'Belum Ada Perangkat',
          description: isAdmin
              ? 'Tekan tombol di bawah untuk mendaftarkan modul ESP32 baru ke server.'
              : 'Hubungi admin rumah untuk menambahkan modul perangkat baru.',
          action: isAdmin
              ? AppButton(
                  label: 'Tambah Perangkat Pertama',
                  icon: Icon(PhosphorIcons.plus(), size: AppDimensions.iconSizeSm),
                  onPressed: () async {
                    final created = await Navigator.of(context).push<bool>(
                      MaterialPageRoute(builder: (_) => const AddDeviceScreen()),
                    );
                    if (created == true) _fetchDevices();
                  },
                )
              : null,
        ),
      ],
    );
  }

  Widget _buildDeviceCard(Map<String, dynamic> dev, Color text, Color textSec, bool isDark) {
    final devId = dev['id'] as String;
    final name = dev['name'] as String? ?? devId;
    final room = dev['room'] as String? ?? 'Umum';
    final isOnline = dev['is_online'] as bool? ?? false;
    final channels = dev['channels'] as List<dynamic>? ?? [];

    final switchChannels = channels.where((c) {
      final t = c['channel_type'] as String;
      return t == 'switch' || t == 'relay' || t == 'buzzer';
    }).toList();

    final sensorChannels = channels.where((c) {
      final t = c['channel_type'] as String;
      return t == 'gas_sensor' || t == 'light_sensor';
    }).toList();

    final history = _telemetryHistory[devId] ?? [];

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header Perangkat
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name,
                    style: AppTypography.body(text, weight: FontWeight.w600, size: AppTypography.textMd),
                  ),
                  const SizedBox(height: AppSpacing.space1),
                  Row(
                    children: [
                      Icon(PhosphorIcons.house(), size: AppDimensions.iconSizeSm, color: textSec),
                      const SizedBox(width: AppSpacing.space1),
                      Text(room, style: AppTypography.body(textSec, size: AppTypography.textXs)),
                      const SizedBox(width: AppSpacing.space2),
                      Text('•', style: AppTypography.body(textSec, size: AppTypography.textXs)),
                      const SizedBox(width: AppSpacing.space2),
                      Text(devId, style: AppTypography.mono(textSec, size: AppTypography.textXs)),
                    ],
                  ),
                ],
              ),
              AppBadge(
                label: isOnline ? 'ONLINE' : 'OFFLINE',
                variant: isOnline ? AppBadgeVariant.ok : AppBadgeVariant.danger,
              ),
            ],
          ),

          // Kanal Saklar / Relay
          if (switchChannels.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.space4),
            Divider(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
            const SizedBox(height: AppSpacing.space2),
            ...switchChannels.map((c) {
              final chKey = c['channel_key'] as String;
              final chName = c['name'] as String;
              final currentValStr = c['current_value']?.toString().toLowerCase() ?? 'false';
              final isOn = currentValStr == 'true';

              return Padding(
                padding: const EdgeInsets.symmetric(vertical: AppSpacing.space2),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Icon(
                          chKey.contains('relay')
                              ? PhosphorIcons.fan()
                              : chKey.contains('buzzer')
                                  ? PhosphorIcons.bellRinging()
                                  : PhosphorIcons.lightbulb(),
                          size: AppDimensions.iconSizeSm,
                          color: isOn ? (isDark ? AppColors.darkAccent : AppColors.lightAccent) : textSec,
                        ),
                        const SizedBox(width: AppSpacing.space2),
                        Text(
                          chName,
                          style: AppTypography.body(text, weight: FontWeight.w500, size: AppTypography.textSm),
                        ),
                      ],
                    ),
                    AppSwitch(
                      value: isOn,
                      onChanged: (newVal) {
                        if (isOnline) {
                          _toggleChannel(devId, chKey, isOn);
                        }
                      },
                    ),
                  ],
                ),
              );
            }),
          ],

          // Kanal Sensor & Grafik Riwayat
          if (sensorChannels.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.space2),
            Divider(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
            const SizedBox(height: AppSpacing.space2),
            ...sensorChannels.map((s) {
              final sKey = s['channel_key'] as String;
              final sName = s['name'] as String;
              final valStr = s['current_value']?.toString() ?? '0';
              final isGas = sKey.contains('mq2') || sKey.contains('gas');
              final numVal = double.tryParse(valStr) ?? 0.0;
              final isDanger = isGas && numVal >= 1500;

              return Padding(
                padding: const EdgeInsets.symmetric(vertical: AppSpacing.space2),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Icon(
                          isGas ? PhosphorIcons.warning() : PhosphorIcons.sun(),
                          size: AppDimensions.iconSizeSm,
                          color: isDanger ? AppColors.statusDanger : textSec,
                        ),
                        const SizedBox(width: AppSpacing.space2),
                        Text(
                          sName,
                          style: AppTypography.body(text, size: AppTypography.textSm),
                        ),
                      ],
                    ),
                    Row(
                      children: [
                        if (isDanger) ...[
                          const AppBadge(label: 'BAHAYA GAS', variant: AppBadgeVariant.danger),
                          const SizedBox(width: AppSpacing.space2),
                        ],
                        Text(
                          isGas ? '$valStr PPM' : (numVal == 1.0 || valStr == 'true' ? 'GELAP' : 'TERANG'),
                          style: AppTypography.mono(
                            isDanger ? AppColors.statusDanger : text,
                            weight: FontWeight.w600,
                            size: AppTypography.textSm,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              );
            }),

            // Grafik Sparkline Riwayat Sederhana (Dibuat murni dengan Container token)
            if (history.isNotEmpty) ...[
              const SizedBox(height: AppSpacing.space3),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Riwayat Sensor (10 Titik Terakhir):',
                    style: AppTypography.body(textSec, size: AppTypography.textXs),
                  ),
                  Text(
                    '${history.last.toStringAsFixed(0)} raw',
                    style: AppTypography.mono(textSec, size: AppTypography.textXs),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.space2),
              _buildSimpleSparkline(history, isDark),
            ],
          ],
        ],
      ),
    );
  }

  Widget _buildSimpleSparkline(List<double> values, bool isDark) {
    if (values.isEmpty) return const SizedBox.shrink();

    final maxVal = values.reduce((a, b) => a > b ? a : b);
    final minVal = values.reduce((a, b) => a < b ? a : b);
    final range = (maxVal - minVal) == 0 ? 1.0 : (maxVal - minVal);

    return Container(
      height: AppDimensions.controlHeight,
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.space2,
        vertical: AppSpacing.space1,
      ),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkSurface : AppColors.lightSurface,
        borderRadius: AppRadius.borderSm,
        border: Border.all(
          color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
          width: AppDimensions.borderWidth,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: values.map((val) {
          final normalized = ((val - minVal) / range).clamp(0.15, 1.0);
          final isHigh = val >= 1500;
          final barColor = isHigh
              ? AppColors.statusDanger
              : (isDark ? AppColors.darkAccent : AppColors.lightAccent);

          return Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space1 / 2),
              child: Container(
                height: (AppDimensions.controlHeight - AppSpacing.space2) * normalized,
                decoration: BoxDecoration(
                  color: barColor,
                  borderRadius: AppRadius.borderSm,
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}
