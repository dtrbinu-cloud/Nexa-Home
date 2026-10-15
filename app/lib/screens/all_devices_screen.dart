import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_badge.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_switch.dart';
import 'package:app/components/app_top_bar.dart';
import 'package:app/components/empty_state.dart';
import 'package:app/core/api_client.dart';
import 'package:app/screens/device_detail_screen.dart';
import 'package:app/theme/tokens.dart';

class AllDevicesScreen extends ConsumerStatefulWidget {
  const AllDevicesScreen({super.key});

  @override
  ConsumerState<AllDevicesScreen> createState() => _AllDevicesScreenState();
}

class _AllDevicesScreenState extends ConsumerState<AllDevicesScreen> {
  bool _isLoading = true;
  List<dynamic> _devices = [];
  String _selectedFilter = 'Semua';
  final _filterOptions = const ['Semua', 'Lampu', 'Kipas', 'Sensor', 'Alarm'];

  @override
  void initState() {
    super.initState();
    _fetchDevices();
  }

  Future<void> _fetchDevices() async {
    setState(() => _isLoading = true);
    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.get('/api/devices');
      if (res.statusCode == 200 && mounted) {
        setState(() {
          _devices = res.data['devices'] as List<dynamic>? ?? [];
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _toggleChannel(Map<String, dynamic> device, Map<String, dynamic> channel) async {
    final devId = device['id'] as String;
    final chKey = channel['channel_key'] as String;
    final currentStr = channel['current_value']?.toString() ?? 'false';
    final currentBool = currentStr.toLowerCase() == 'true' || currentStr == '1';
    final nextVal = !currentBool;

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
      if (mounted) {
        setState(() {
          channel['current_value'] = currentBool.toString();
        });
      }
    }
  }

  PhosphorIconData _getIconForChannel(String type, String key) {
    if (type == 'switch' || key.contains('lamp')) return PhosphorIcons.lightbulb();
    if (type == 'relay' || key.contains('fan')) return PhosphorIcons.fan();
    if (type == 'buzzer' || key.contains('alarm')) return PhosphorIcons.shield();
    if (type == 'gas_sensor') return PhosphorIcons.gauge();
    if (type == 'light_sensor') return PhosphorIcons.sun();
    return PhosphorIcons.cpu();
  }

  bool _matchesFilter(String type, String key) {
    if (_selectedFilter == 'Semua') return true;
    if (_selectedFilter == 'Lampu') return type == 'switch' || key.contains('lamp');
    if (_selectedFilter == 'Kipas') return type == 'relay' || key.contains('fan');
    if (_selectedFilter == 'Sensor') return type == 'gas_sensor' || type == 'light_sensor' || key.contains('mq2') || key.contains('ldr');
    if (_selectedFilter == 'Alarm') return type == 'buzzer' || key.contains('alarm');
    return true;
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkBg : AppColors.lightBg;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final subtle = isDark ? AppColors.darkSubtle : AppColors.lightSubtle;

    // Kelompokkan channels per ruangan
    final roomMap = <String, List<Map<String, dynamic>>>{};
    for (final d in _devices) {
      final room = d['room']?.toString() ?? 'Umum';
      final channels = d['channels'] as List<dynamic>? ?? [];

      for (final c in channels) {
        final type = c['channel_type']?.toString() ?? '';
        final key = c['channel_key']?.toString() ?? '';

        if (_matchesFilter(type, key)) {
          roomMap.putIfAbsent(room, () => []).add({
            'device': d,
            'channel': c,
          });
        }
      }
    }

    return Scaffold(
      backgroundColor: bg,
      appBar: AppTopBar(
        title: 'Semua perangkat',
        actions: [
          IconButton(
            tooltip: 'Cari',
            icon: PhosphorIcon(
              PhosphorIcons.magnifyingGlass(),
              size: AppDimensions.iconSizeSm,
              color: text,
            ),
            onPressed: () {},
          ),
          IconButton(
            tooltip: 'Filter',
            icon: PhosphorIcon(
              PhosphorIcons.slidersHorizontal(),
              size: AppDimensions.iconSizeSm,
              color: text,
            ),
            onPressed: () {},
          ),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _fetchDevices,
          color: isDark ? AppColors.darkAccent : AppColors.lightAccent,
          backgroundColor: isDark ? AppColors.darkSurface : AppColors.lightSurface,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMargin),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: AppSpacing.space2),

                // Filter chips horizontal
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: _filterOptions.map((f) {
                      return Padding(
                        padding: const EdgeInsets.only(right: AppSpacing.space2),
                        child: AppChip(
                          label: f,
                          isSelected: _selectedFilter == f,
                          onTap: () => setState(() => _selectedFilter = f),
                        ),
                      );
                    }).toList(),
                  ),
                ),

                const SizedBox(height: AppDimensions.sectionGap),

                if (_isLoading)
                  const Padding(
                    padding: EdgeInsets.all(AppSpacing.space8),
                    child: Center(child: CircularProgressIndicator()),
                  )
                else if (roomMap.isEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: AppSpacing.space8),
                    child: EmptyState(
                      icon: PhosphorIcon(
                        PhosphorIcons.cpu(),
                        size: 48,
                        color: textSec,
                      ),
                      title: 'Tidak ada perangkat',
                      description: 'Tidak ada perangkat yang cocok dengan filter "$_selectedFilter".',
                    ),
                  )
                else
                  ...roomMap.entries.map((entry) {
                    final roomName = entry.key;
                    final items = entry.value;

                    // Hitung yang aktif
                    int activeCount = 0;
                    for (final item in items) {
                      final ch = item['channel'] as Map<String, dynamic>;
                      final valStr = ch['current_value']?.toString() ?? 'false';
                      if (valStr.toLowerCase() == 'true' || valStr == '1') {
                        activeCount++;
                      }
                    }

                    return Padding(
                      padding: const EdgeInsets.only(bottom: AppDimensions.sectionGap),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Header bagian: Ruang (huruf biasa) + hitungan mono
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Expanded(
                                child: Text(
                                  roomName,
                                  style: AppTypography.body(
                                    textSec,
                                    size: AppTypography.textXs,
                                    weight: FontWeight.w600,
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              Row(
                                children: [
                                  Text(
                                    '$activeCount ',
                                    style: AppTypography.mono(
                                      textSec,
                                      size: AppTypography.textXs,
                                      weight: FontWeight.w600,
                                    ),
                                  ),
                                  Text(
                                    'menyala',
                                    style: AppTypography.body(
                                      textSec,
                                      size: AppTypography.textXs,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                          const SizedBox(height: AppSpacing.space3),

                          // Kartu berisi baris-baris perangkat
                          AppCard(
                            padding: EdgeInsets.zero,
                            child: Column(
                              children: items.asMap().entries.map((e) {
                                final idx = e.key;
                                final item = e.value;
                                final dev = item['device'] as Map<String, dynamic>;
                                final ch = item['channel'] as Map<String, dynamic>;
                                final isLast = idx == items.length - 1;

                                final devId = dev['id']?.toString() ?? '';
                                final devName = ch['name']?.toString() ?? dev['name']?.toString() ?? 'Perangkat';
                                final isOnline = dev['is_online'] == true;
                                final valStr = ch['current_value']?.toString() ?? 'false';
                                final isOn = valStr.toLowerCase() == 'true' || valStr == '1';
                                final chType = ch['channel_type']?.toString() ?? '';
                                final chKey = ch['channel_key']?.toString() ?? '';

                                final isSensor = chType == 'gas_sensor' || chType == 'light_sensor';
                                final iconData = _getIconForChannel(chType, chKey);

                                final rawTime = dev['last_seen_at']?.toString() ?? '';
                                String timeOnly = '19:45';
                                if (rawTime.contains('T')) {
                                  final parts = rawTime.split('T')[1].split(':');
                                  if (parts.length >= 2) timeOnly = '${parts[0]}:${parts[1]}';
                                }

                                return InkWell(
                                  onTap: () {
                                    Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder: (_) => DeviceDetailScreen(
                                          deviceId: devId,
                                        ),
                                      ),
                                    );
                                  },
                                  child: Container(
                                    constraints: const BoxConstraints(minHeight: AppDimensions.listRowMinHeight),
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
                                    child: Opacity(
                                      opacity: isOnline ? 1.0 : 0.6,
                                      child: Row(
                                        children: [
                                          // Circle Icon
                                          Container(
                                            width: 40.0,
                                            height: 40.0,
                                            decoration: BoxDecoration(
                                              color: subtle,
                                              shape: BoxShape.circle,
                                            ),
                                            alignment: Alignment.center,
                                            child: PhosphorIcon(
                                              iconData,
                                              size: AppDimensions.iconSizeSm,
                                              color: isOnline && isOn
                                                  ? (isDark ? AppColors.darkAccent : AppColors.lightAccent)
                                                  : textSec,
                                            ),
                                          ),
                                          const SizedBox(width: AppSpacing.space3),

                                          // Title & status line
                                          Expanded(
                                            child: Column(
                                              crossAxisAlignment: CrossAxisAlignment.start,
                                              children: [
                                                Text(
                                                  devName,
                                                  style: AppTypography.body(
                                                    text,
                                                    size: AppTypography.textSm,
                                                    weight: FontWeight.w600,
                                                  ),
                                                ),
                                                const SizedBox(height: 2.0),
                                                Row(
                                                  children: [
                                                    Container(
                                                      width: 6.0,
                                                      height: 6.0,
                                                      decoration: BoxDecoration(
                                                        color: isOnline ? AppColors.statusOk : textSec,
                                                        shape: BoxShape.circle,
                                                      ),
                                                    ),
                                                    const SizedBox(width: 6.0),
                                                    Text(
                                                      isOnline ? 'Online ' : 'Terputus ',
                                                      style: AppTypography.body(
                                                        textSec,
                                                        size: AppTypography.textXs,
                                                      ),
                                                    ),
                                                    if (isOnline)
                                                      Text(
                                                        timeOnly,
                                                        style: AppTypography.mono(
                                                          textSec,
                                                          size: AppTypography.textXs,
                                                        ),
                                                      ),
                                                  ],
                                                ),
                                              ],
                                            ),
                                          ),

                                          // Trailing action: toggle atau sensor value
                                          if (isSensor) ...[
                                            // Nilai sensor (angka mentah mono tanpa satuan!)
                                            Container(
                                              padding: const EdgeInsets.symmetric(
                                                horizontal: AppSpacing.space3,
                                                vertical: 6.0,
                                              ),
                                              decoration: BoxDecoration(
                                                color: subtle,
                                                borderRadius: AppRadius.borderChip,
                                              ),
                                              child: Text(
                                                chType == 'gas_sensor'
                                                    ? (valStr.isEmpty ? '412' : valStr)
                                                    : (valStr.toLowerCase() == 'true' || valStr == '1' ? 'Terang' : 'Gelap'),
                                                style: chType == 'gas_sensor'
                                                    ? AppTypography.mono(text, size: AppTypography.textXs)
                                                    : AppTypography.body(text, size: AppTypography.textXs),
                                              ),
                                            ),
                                          ] else if (isOnline) ...[
                                            AppSwitch(
                                              value: isOn,
                                              onChanged: (_) => _toggleChannel(dev, ch),
                                              semanticLabel: 'Saklar $devName',
                                            ),
                                          ] else ...[
                                            Text(
                                              'Terputus',
                                              style: AppTypography.body(
                                                textSec,
                                                size: AppTypography.textXs,
                                              ),
                                            ),
                                          ],
                                        ],
                                      ),
                                    ),
                                  ),
                                );
                              }).toList(),
                            ),
                          ),
                        ],
                      ),
                    );
                  }),

                const SizedBox(height: AppSpacing.space6),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
