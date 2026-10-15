import 'package:flutter/material.dart';
import 'package:camera_app/core/api.dart';
import 'package:camera_app/core/network_validator.dart';
import 'package:camera_app/core/storage.dart';
import 'package:camera_app/screens/camera_live_screen.dart';
import 'package:camera_app/theme/tokens.dart';

class PairingScreen extends StatefulWidget {
  const PairingScreen({super.key});

  @override
  State<PairingScreen> createState() => _PairingScreenState();
}

class _PairingScreenState extends State<PairingScreen> {
  final _serverUrlController = TextEditingController(text: 'http://192.168.1.50:8000');
  final _codeController = TextEditingController();

  String _selectedRoom = 'Ruang Tamu';
  final List<String> _rooms = [
    'Ruang Tamu',
    'Garasi',
    'Teras Depan',
    'Kamar Utama',
    'Dapur',
    'Halaman Belakang',
  ];

  bool _isLoading = false;
  String? _errorMessage;
  bool _showBatteryGuide = false;

  @override
  void dispose() {
    _serverUrlController.dispose();
    _codeController.dispose();
    super.dispose();
  }

  Future<void> _handlePairing() async {
    setState(() {
      _errorMessage = null;
    });

    final serverUrl = _serverUrlController.text.trim();
    final code = _codeController.text.trim().toUpperCase();

    // Validasi URL
    final urlError = NetworkValidator.validateServerUrl(serverUrl);
    if (urlError != null) {
      setState(() => _errorMessage = urlError);
      return;
    }

    if (code.isEmpty) {
      setState(() => _errorMessage = 'Kode pairing wajib diisi.');
      return;
    }

    setState(() => _isLoading = true);

    try {
      final pairData = await CameraApiClient.pairCamera(
        serverUrl: serverUrl,
        pairingCode: code,
      );

      final camId = pairData['camera_id'] as String;
      final camToken = pairData['camera_token'] as String;
      final camName = (pairData['camera_name'] as String?) ?? 'Kamera HP';
      final roomId = (pairData['room_id'] as String?) ?? _selectedRoom;

      await CameraStorage.savePairingData(
        serverUrl: serverUrl,
        cameraId: camId,
        cameraToken: camToken,
        cameraName: camName,
        roomId: roomId,
      );

      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const CameraLiveScreen()),
        );
      }
    } catch (e) {
      setState(() {
        _errorMessage = e.toString().replaceAll('Exception: ', '');
      });
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.darkBg,
      appBar: AppBar(
        title: Text(
          'Pairing Kamera HP',
          style: AppTypography.body(AppColors.darkText, size: AppTypography.textLg, weight: FontWeight.w600),
        ),
        backgroundColor: AppColors.darkSurface,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.space4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header Info
            Container(
              padding: const EdgeInsets.all(AppSpacing.space4),
              decoration: const BoxDecoration(
                color: AppColors.darkSurface,
                borderRadius: AppRadius.borderMd,
                border: Border.fromBorderSide(BorderSide(color: AppColors.darkBorder, width: AppDimensions.borderWidth)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Jadikan HP Ini Kamera Pengawas',
                    style: AppTypography.body(AppColors.darkText, size: AppTypography.textMd, weight: FontWeight.w600),
                  ),
                  const SizedBox(height: AppSpacing.space1),
                  Text(
                    'Dapatkan kode pairing sekali pakai dari menu Kamera di aplikasi utama admin (Rumah) pada laptop atau HP pengelola.',
                    style: AppTypography.body(AppColors.darkTextSecondary, size: AppTypography.textXs),
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.space4),

            // Form Alamat Server
            Text(
              'Alamat Server LAN',
              style: AppTypography.body(AppColors.darkTextSecondary, size: AppTypography.textXs, weight: FontWeight.w500),
            ),
            const SizedBox(height: AppSpacing.space1),
            TextField(
              controller: _serverUrlController,
              style: AppTypography.body(AppColors.darkText, size: AppTypography.textSm),
              decoration: InputDecoration(
                hintText: 'http://192.168.1.50:8000',
                hintStyle: AppTypography.body(AppColors.darkTextSecondary, size: AppTypography.textSm),
                filled: true,
                fillColor: AppColors.darkSurface,
                contentPadding: const EdgeInsets.symmetric(horizontal: AppSpacing.space4, vertical: AppSpacing.space2),
                enabledBorder: const OutlineInputBorder(
                  borderRadius: AppRadius.borderSm,
                  borderSide: BorderSide(color: AppColors.darkBorder),
                ),
                focusedBorder: const OutlineInputBorder(
                  borderRadius: AppRadius.borderSm,
                  borderSide: BorderSide(color: AppColors.darkAccent),
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.space4),

            // Form Kode Pairing
            Text(
              'Kode Pairing Sekali Pakai',
              style: AppTypography.body(AppColors.darkTextSecondary, size: AppTypography.textXs, weight: FontWeight.w500),
            ),
            const SizedBox(height: AppSpacing.space1),
            TextField(
              controller: _codeController,
              textCapitalization: TextCapitalization.characters,
              style: AppTypography.mono(AppColors.darkAccent, size: AppTypography.textMd, weight: FontWeight.w600),
              decoration: InputDecoration(
                hintText: 'CAM-A1B2C3',
                hintStyle: AppTypography.mono(AppColors.darkTextSecondary, size: AppTypography.textMd),
                filled: true,
                fillColor: AppColors.darkSurface,
                contentPadding: const EdgeInsets.symmetric(horizontal: AppSpacing.space4, vertical: AppSpacing.space2),
                enabledBorder: const OutlineInputBorder(
                  borderRadius: AppRadius.borderSm,
                  borderSide: BorderSide(color: AppColors.darkBorder),
                ),
                focusedBorder: const OutlineInputBorder(
                  borderRadius: AppRadius.borderSm,
                  borderSide: BorderSide(color: AppColors.darkAccent),
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.space4),

            // Pilihan Ruangan
            Text(
              'Penempatan Ruangan',
              style: AppTypography.body(AppColors.darkTextSecondary, size: AppTypography.textXs, weight: FontWeight.w500),
            ),
            const SizedBox(height: AppSpacing.space1),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space4),
              decoration: const BoxDecoration(
                color: AppColors.darkSurface,
                borderRadius: AppRadius.borderSm,
                border: Border.fromBorderSide(BorderSide(color: AppColors.darkBorder)),
              ),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: _selectedRoom,
                  dropdownColor: AppColors.darkSurface,
                  isExpanded: true,
                  style: AppTypography.body(AppColors.darkText, size: AppTypography.textSm),
                  items: _rooms.map((r) => DropdownMenuItem(value: r, child: Text(r))).toList(),
                  onChanged: (val) {
                    if (val != null) setState(() => _selectedRoom = val);
                  },
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.space4),

            // Anjuran Mematikan Optimasi Baterai (Penting untuk Android Bekas)
            Container(
              padding: const EdgeInsets.all(AppSpacing.space4),
              decoration: const BoxDecoration(
                color: AppColors.darkSurface,
                borderRadius: AppRadius.borderMd,
                border: Border.fromBorderSide(BorderSide(color: AppColors.darkBorder)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 8,
                        height: 8,
                        decoration: const BoxDecoration(
                          color: AppColors.statusWarn,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: AppSpacing.space1),
                      Expanded(
                        child: Text(
                          'PENTING: Matikan Optimasi Baterai',
                          style: AppTypography.body(AppColors.darkText, size: AppTypography.textSm, weight: FontWeight.w600),
                        ),
                      ),
                      IconButton(
                        icon: Icon(
                          _showBatteryGuide ? Icons.expand_less : Icons.expand_more,
                          color: AppColors.darkTextSecondary,
                        ),
                        onPressed: () => setState(() => _showBatteryGuide = !_showBatteryGuide),
                      ),
                    ],
                  ),
                  Text(
                    'Agar kamera tetap aktif saat layar terkunci dan tidak dimatikan paksa oleh sistem Android (Doze Mode).',
                    style: AppTypography.body(AppColors.darkTextSecondary, size: AppTypography.textXs),
                  ),
                  if (_showBatteryGuide) ...[
                    const SizedBox(height: AppSpacing.space2),
                    const Divider(color: AppColors.darkBorder),
                    const SizedBox(height: AppSpacing.space1),
                    Text(
                      'Langkah per merek HP:\n'
                      '• Xiaomi/MIUI: Pengaturan > Kelola Aplikasi > Rumah Camera > Penghemat Baterai > "Tidak ada pembatasan" & aktifkan Mulai Otomatis.\n'
                      '• Samsung/OneUI: Pengaturan > Aplikasi > Rumah Camera > Baterai > "Tidak Dibatasi".\n'
                      '• Oppo/Realme: Info Aplikasi > Konsumsi Baterai > Izinkan aktivitas latar belakang.\n'
                      '• Vivo: Info Aplikasi > Baterai > Konsumsi daya latar belakang tinggi.',
                      style: AppTypography.body(AppColors.darkText, size: AppTypography.textXs),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.space4),

            // Pesan Kesalahan jika ada
            if (_errorMessage != null) ...[
              Container(
                padding: const EdgeInsets.all(AppSpacing.space2),
                decoration: const BoxDecoration(
                  color: AppColors.darkSurface,
                  borderRadius: AppRadius.borderSm,
                  border: Border.fromBorderSide(BorderSide(color: AppColors.statusDanger)),
                ),
                child: Text(
                  _errorMessage!,
                  style: AppTypography.body(AppColors.statusDanger, size: AppTypography.textXs),
                ),
              ),
              const SizedBox(height: AppSpacing.space4),
            ],

            // Tombol Pasangkan
            SizedBox(
              height: 48,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.darkAccent,
                  foregroundColor: AppColors.darkSurface,
                  shape: const RoundedRectangleBorder(borderRadius: AppRadius.borderSm),
                ),
                onPressed: _isLoading ? null : _handlePairing,
                child: _isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Text(
                        'PASANGKAN KAMERA SEKARANG',
                        style: AppTypography.body(AppColors.darkSurface, size: AppTypography.textSm, weight: FontWeight.w600),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
