import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_badge.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_input.dart';
import 'package:app/components/app_switch.dart';
import 'package:app/components/app_toast.dart';
import 'package:app/core/api_client.dart';
import 'package:app/theme/tokens.dart';

class ChannelAdminScreen extends StatefulWidget {
  const ChannelAdminScreen({super.key});

  @override
  State<ChannelAdminScreen> createState() => _ChannelAdminScreenState();
}

class _ChannelAdminScreenState extends State<ChannelAdminScreen> {
  bool _isLoading = true;
  List<Map<String, dynamic>> _channels = [];
  final Map<int, TextEditingController> _aliasControllers = {};

  @override
  void initState() {
    super.initState();
    _loadChannels();
  }

  @override
  void dispose() {
    for (final c in _aliasControllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _loadChannels() async {
    setState(() => _isLoading = true);
    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.get('/api/channels');
      final list = (res.data['channels'] as List).cast<Map<String, dynamic>>();
      _channels = list;
      for (final ch in _channels) {
        final id = ch['id'] as int;
        _aliasControllers[id] = TextEditingController(text: ch['alias'] as String? ?? '');
      }
    } catch (e) {
      if (mounted) {
        AppToast.show(context, 'Gagal memuat daftar kanal.', isError: true);
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _saveChannel(Map<String, dynamic> ch) async {
    final id = ch['id'] as int;
    final aliasText = _aliasControllers[id]?.text.trim() ?? '';
    try {
      final dio = await ApiClient.getInstance();
      await dio.patch(
        '/api/channels/$id',
        data: {
          'alias': aliasText.isEmpty ? null : aliasText,
          'is_sensitive': ch['is_sensitive'],
          'allowed_for_child': ch['allowed_for_child'],
        },
      );
      if (mounted) {
        AppToast.show(context, 'Pengaturan ${ch['name']} berhasil disimpan.');
      }
    } catch (e) {
      if (mounted) {
        AppToast.show(context, 'Gagal menyimpan pengaturan kanal.', isError: true);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          'Manajemen Kanal & Izin',
          style: AppTypography.body(text, size: AppTypography.textLg, weight: FontWeight.w600),
        ),
      ),

      body: SafeArea(
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _channels.isEmpty
                ? Center(
                    child: Text(
                      'Tidak ada kanal terdaftar.',
                      style: AppTypography.body(textSec),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(AppSpacing.space4),
                    itemCount: _channels.length,
                    itemBuilder: (context, idx) {
                      final ch = _channels[idx];
                      final id = ch['id'] as int;
                      final isSensitive = ch['is_sensitive'] as bool? ?? false;
                      final allowedChild = ch['allowed_for_child'] as bool? ?? true;

                      return Padding(
                        padding: const EdgeInsets.only(bottom: AppSpacing.space4),
                        child: AppCard(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          ch['name'] as String? ?? 'Kanal #$id',
                                          style: AppTypography.body(
                                            text,
                                            size: AppTypography.textMd,
                                            weight: FontWeight.w600,
                                          ),
                                        ),
                                        Text(
                                          'Perangkat: ${ch['device_name'] ?? ch['device_id']}',
                                          style: AppTypography.body(
                                            textSec,
                                            size: AppTypography.textXs,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  AppBadge(
                                    label: ch['channel_type'] as String? ?? 'relay',
                                    variant: AppBadgeVariant.neutral,
                                  ),
                                ],
                              ),
                              const SizedBox(height: AppSpacing.space3),
                              AppInput(
                                label: 'Nama Panggilan / Alias (Asisten)',
                                hint: 'misal: lampu kamar, kipas',
                                controller: _aliasControllers[id],
                                prefixIcon: Icon(
                                  PhosphorIcons.tag(),
                                  size: AppDimensions.iconSizeSm,
                                  color: textSec,
                                ),
                              ),
                              const SizedBox(height: AppSpacing.space3),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        'Kanal Sensitif',
                                        style: AppTypography.body(
                                          text,
                                          size: AppTypography.textSm,
                                          weight: FontWeight.w500,
                                        ),
                                      ),
                                      Text(
                                        'Perlu konfirmasi eksplisit Ya/Batal',
                                        style: AppTypography.body(
                                          textSec,
                                          size: AppTypography.textXs,
                                        ),
                                      ),
                                    ],
                                  ),
                                  AppSwitch(
                                    value: isSensitive,
                                    onChanged: (val) {
                                      setState(() {
                                        ch['is_sensitive'] = val;
                                      });
                                    },
                                  ),
                                ],
                              ),
                              const Divider(height: AppSpacing.space4),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        'Izin Kontrol Anak',
                                        style: AppTypography.body(
                                          text,
                                          size: AppTypography.textSm,
                                          weight: FontWeight.w500,
                                        ),
                                      ),
                                      Text(
                                        'Akun child dapat mengontrol kanal ini',
                                        style: AppTypography.body(
                                          textSec,
                                          size: AppTypography.textXs,
                                        ),
                                      ),
                                    ],
                                  ),
                                  AppSwitch(
                                    value: allowedChild,
                                    onChanged: (val) {
                                      setState(() {
                                        ch['allowed_for_child'] = val;
                                      });
                                    },
                                  ),
                                ],
                              ),
                              const SizedBox(height: AppSpacing.space3),
                              Align(
                                alignment: Alignment.centerRight,
                                child: AppButton(
                                  label: 'Simpan Kanal',
                                  variant: AppButtonVariant.primary,
                                  onPressed: () => _saveChannel(ch),
                                  icon: Icon(
                                    PhosphorIcons.check(),
                                    size: AppDimensions.iconSizeSm,
                                    color: AppColors.lightSurface,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
      ),
    );
  }
}
