import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_badge.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_input.dart';
import 'package:app/components/app_toast.dart';
import 'package:app/core/api_client.dart';
import 'package:app/theme/tokens.dart';

class AddDeviceScreen extends StatefulWidget {
  const AddDeviceScreen({super.key});

  @override
  State<AddDeviceScreen> createState() => _AddDeviceScreenState();
}

class _AddDeviceScreenState extends State<AddDeviceScreen> {
  final _idController = TextEditingController();
  final _nameController = TextEditingController();
  final _roomController = TextEditingController();

  bool _isLoading = false;
  Map<String, dynamic>? _createdCredentials;

  @override
  void dispose() {
    _idController.dispose();
    _nameController.dispose();
    _roomController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final devId = _idController.text.trim();
    final name = _nameController.text.trim();
    final room = _roomController.text.trim();

    if (devId.isEmpty || name.isEmpty) {
      AppToast.show(context, 'ID dan nama perangkat wajib diisi.');
      return;
    }

    setState(() => _isLoading = true);

    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.post(
        '/api/devices',
        data: {
          'id': devId,
          'name': name,
          'room': room.isEmpty ? 'Umum' : room,
          'device_type': 'esp32',
        },
      );

      if (res.statusCode == 201) {
        setState(() {
          _createdCredentials = res.data['mqtt_credentials'] as Map<String, dynamic>?;
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        AppToast.show(context, 'Gagal menambah perangkat. Pastikan ID belum digunakan.');
      }
    }
  }

  void _copyToClipboard(String label, String value) {
    Clipboard.setData(ClipboardData(text: value));
    AppToast.show(context, '$label disalin ke papan klip.');
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          _createdCredentials == null ? 'Tambah Perangkat' : 'Kredensial MQTT',
          style: AppTypography.body(text, weight: FontWeight.w600, size: AppTypography.textMd),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.space4),
          child: _createdCredentials == null ? _buildForm(text, textSec) : _buildCredentialsView(text, textSec),
        ),
      ),
    );
  }

  Widget _buildForm(Color text, Color textSec) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Daftarkan modul ESP32 baru ke server. Sistem akan secara otomatis membuatkan username dan password MQTT unik.',
          style: AppTypography.body(textSec, size: AppTypography.textSm),
        ),
        const SizedBox(height: AppSpacing.space4),
        AppInput(
          controller: _idController,
          label: 'ID Perangkat (Alfanumerik)',
          hint: 'contoh: esp32_tamu',
          prefixIcon: Icon(PhosphorIcons.fingerprint(), size: AppDimensions.iconSizeSm),
        ),
        const SizedBox(height: AppSpacing.space3),
        AppInput(
          controller: _nameController,
          label: 'Nama Perangkat',
          hint: 'contoh: ESP32 Ruang Tamu',
          prefixIcon: Icon(PhosphorIcons.tag(), size: AppDimensions.iconSizeSm),
        ),
        const SizedBox(height: AppSpacing.space3),
        AppInput(
          controller: _roomController,
          label: 'Lokasi / Ruangan',
          hint: 'contoh: Ruang Tamu',
          prefixIcon: Icon(PhosphorIcons.house(), size: AppDimensions.iconSizeSm),
        ),
        const SizedBox(height: AppSpacing.space6),
        AppButton(
          label: 'Daftarkan Perangkat',
          onPressed: _submit,
          isLoading: _isLoading,
          icon: Icon(PhosphorIcons.plusCircle(), size: AppDimensions.iconSizeSm),
        ),
      ],
    );
  }

  Widget _buildCredentialsView(Color text, Color textSec) {
    final c = _createdCredentials!;
    final user = c['username']?.toString() ?? '';
    final pass = c['password']?.toString() ?? '';
    final prefix = c['topic_prefix']?.toString() ?? '';
    final host = c['broker_host']?.toString() ?? '127.0.0.1';
    final port = c['broker_port']?.toString() ?? '1883';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const AppBadge(
          label: 'SIMPAN KREDENSIAL INI',
          variant: AppBadgeVariant.warn,
        ),
        const SizedBox(height: AppSpacing.space2),
        Text(
          'Kredensial MQTT berikut hanya ditampilkan satu kali. Salin ke secrets.h pada firmware ESP32:',
          style: AppTypography.body(textSec, size: AppTypography.textSm),
        ),
        const SizedBox(height: AppSpacing.space4),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildCredRow('Broker Host', host, text, textSec),
              const SizedBox(height: AppSpacing.space2),
              _buildCredRow('Port', port, text, textSec),
              const SizedBox(height: AppSpacing.space2),
              _buildCredRow('Topic Prefix', prefix, text, textSec),
              const SizedBox(height: AppSpacing.space2),
              _buildCredRow('Username', user, text, textSec),
              const SizedBox(height: AppSpacing.space2),
              _buildCredRow('Password', pass, text, textSec),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.space6),
        AppButton(
          label: 'Salin Seluruh Konfigurasi',
          variant: AppButtonVariant.secondary,
          icon: Icon(PhosphorIcons.copy(), size: AppDimensions.iconSizeSm),
          onPressed: () {
            final dump =
                '#define MQTT_HOST "$host"\n#define MQTT_PORT $port\n#define MQTT_USER "$user"\n#define MQTT_PASS "$pass"\n#define DEVICE_ID "$user"';
            _copyToClipboard('Konfigurasi C++', dump);
          },
        ),
        const SizedBox(height: AppSpacing.space3),
        AppButton(
          label: 'Selesai',
          onPressed: () => Navigator.of(context).pop(true),
        ),
      ],
    );
  }

  Widget _buildCredRow(String label, String value, Color text, Color textSec) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: AppTypography.body(textSec, size: AppTypography.textXs)),
        Row(
          children: [
            Text(value, style: AppTypography.mono(text, size: AppTypography.textXs, weight: FontWeight.w600)),
            const SizedBox(width: AppSpacing.space2),
            GestureDetector(
              onTap: () => _copyToClipboard(label, value),
              child: Icon(PhosphorIcons.copy(), size: AppDimensions.iconSizeSm, color: textSec),
            ),
          ],
        ),
      ],
    );
  }
}
