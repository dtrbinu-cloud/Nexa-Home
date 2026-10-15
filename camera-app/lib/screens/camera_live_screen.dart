import 'dart:async';
import 'package:flutter/material.dart';
import 'package:camera_app/core/storage.dart';
import 'package:camera_app/screens/pairing_screen.dart';
import 'package:camera_app/theme/tokens.dart';
import 'package:wakelock_plus/wakelock_plus.dart';

class CameraLiveScreen extends StatefulWidget {
  const CameraLiveScreen({super.key});

  @override
  State<CameraLiveScreen> createState() => _CameraLiveScreenState();
}

class _CameraLiveScreenState extends State<CameraLiveScreen> with SingleTickerProviderStateMixin {
  String _cameraName = 'Memuat...';
  String _roomId = '';
  String _serverUrl = '';

  bool _isStreaming = true;
  bool _isDimmedMode = false;
  String _connectionStatus = 'TERHUBUNG (LAN WebRTC/RTSP)';

  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;
  Timer? _reconnectTimer;
  int _reconnectAttempts = 0;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 1),
    )..repeat(reverse: true);
    _pulseAnimation = Tween<double>(begin: 0.4, end: 1.0).animate(_pulseController);

    _loadCameraData();
    _enableWakeLock();
  }

  Future<void> _loadCameraData() async {
    final name = await CameraStorage.getCameraName();
    final room = await CameraStorage.getRoomId();
    final url = await CameraStorage.getServerUrl();
    if (mounted) {
      setState(() {
        _cameraName = name ?? 'Kamera Pengawas';
        _roomId = room ?? 'Rumah';
        _serverUrl = url ?? '';
      });
    }
  }

  Future<void> _enableWakeLock() async {
    try {
      await WakelockPlus.enable();
    } catch (_) {}
  }

  Future<void> _disableWakeLock() async {
    try {
      await WakelockPlus.disable();
    } catch (_) {}
  }

  void _toggleStreaming() {
    setState(() {
      _isStreaming = !_isStreaming;
      if (_isStreaming) {
        _connectionStatus = 'TERHUBUNG (LAN WebRTC/RTSP)';
        _enableWakeLock();
      } else {
        _connectionStatus = 'PENYIARAN DIHENTIKAN';
        _disableWakeLock();
      }
    });
  }

  void _triggerSimulatedReconnect() {
    setState(() {
      _connectionStatus = 'MENYAMBUNGKAN ULANG (Mencoba lagi...)';
      _reconnectAttempts++;
    });

    final backoffSeconds = (_reconnectAttempts * 2).clamp(2, 30);
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(Duration(seconds: backoffSeconds), () {
      if (mounted && _isStreaming) {
        setState(() {
          _connectionStatus = 'TERHUBUNG (LAN WebRTC/RTSP)';
          _reconnectAttempts = 0;
        });
      }
    });
  }

  Future<void> _handleUnpair() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.darkSurface,
        title: Text(
          'Putuskan Kamera?',
          style: AppTypography.body(AppColors.darkText, size: AppTypography.textMd, weight: FontWeight.w600),
        ),
        content: Text(
          'Token pairing lokal akan dihapus. Anda perlu memasangkan ulang dari aplikasi utama admin.',
          style: AppTypography.body(AppColors.darkTextSecondary, size: AppTypography.textSm),
        ),
        actions: [
          TextButton(
            child: Text(
              'Batal',
              style: AppTypography.body(AppColors.darkTextSecondary, size: AppTypography.textSm),
            ),
            onPressed: () => Navigator.of(ctx).pop(false),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.statusDanger),
            child: Text(
              'Putuskan',
              style: AppTypography.body(AppColors.darkSurface, size: AppTypography.textSm, weight: FontWeight.w600),
            ),
            onPressed: () => Navigator.of(ctx).pop(true),
          ),
        ],
      ),
    );

    if (confirm == true) {
      await CameraStorage.clear();
      await _disableWakeLock();
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const PairingScreen()),
        );
      }
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _reconnectTimer?.cancel();
    _disableWakeLock();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_isDimmedMode) {
      // Mode Layar Gelap (OLED Battery Saver Mode)
      return GestureDetector(
        onTap: () => setState(() => _isDimmedMode = false),
        child: Scaffold(
          backgroundColor: AppColors.darkBg,
          body: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                FadeTransition(
                  opacity: _pulseAnimation,
                  child: Container(
                    width: 14,
                    height: 14,
                    decoration: const BoxDecoration(
                      color: AppColors.statusDanger,
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.space2),
                Text(
                  'Mode Layar Gelap Aktif (Kamera Tetap Berjalan)',
                  style: AppTypography.body(AppColors.darkTextSecondary, size: AppTypography.textXs),
                ),
                const SizedBox(height: AppSpacing.space1),
                Text(
                  'Ketuk di mana saja untuk menyalakan layar',
                  style: AppTypography.body(AppColors.darkTextSecondary, size: AppTypography.textXs),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.darkBg,
      appBar: AppBar(
        title: Text(
          _cameraName,
          style: AppTypography.body(AppColors.darkText, size: AppTypography.textMd, weight: FontWeight.w600),
        ),
        backgroundColor: AppColors.darkSurface,
        elevation: 0,
        actions: [
          IconButton(
            tooltip: 'Putuskan Pairing',
            icon: const Icon(Icons.link_off, color: AppColors.darkTextSecondary),
            onPressed: _handleUnpair,
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.space4),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Kartu Status Koneksi & Indikator Titik Merah
              Container(
                padding: const EdgeInsets.all(AppSpacing.space4),
                decoration: const BoxDecoration(
                  color: AppColors.darkSurface,
                  borderRadius: AppRadius.borderMd,
                  border: Border.fromBorderSide(BorderSide(color: AppColors.darkBorder, width: AppDimensions.borderWidth)),
                ),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        if (_isStreaming) ...[
                          FadeTransition(
                            opacity: _pulseAnimation,
                            child: Container(
                              width: 14,
                              height: 14,
                              decoration: const BoxDecoration(
                                color: AppColors.statusDanger,
                                shape: BoxShape.circle,
                              ),
                            ),
                          ),
                          const SizedBox(width: AppSpacing.space2),
                          Text(
                            'KAMERA AKTIF MEMANCARKAN STREAM',
                            style: AppTypography.body(AppColors.darkText, size: AppTypography.textSm, weight: FontWeight.w600),
                          ),
                        ] else ...[
                          Container(
                            width: 14,
                            height: 14,
                            decoration: const BoxDecoration(
                              color: AppColors.darkTextSecondary,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: AppSpacing.space2),
                          Text(
                            'KAMERA BERHENTI',
                            style: AppTypography.body(AppColors.darkTextSecondary, size: AppTypography.textSm, weight: FontWeight.w600),
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: AppSpacing.space2),
                    GestureDetector(
                      onTap: _isStreaming ? _triggerSimulatedReconnect : null,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space4, vertical: AppSpacing.space1),
                        decoration: BoxDecoration(
                          color: _isStreaming ? AppColors.darkBg : AppColors.darkSurface,
                          borderRadius: BorderRadius.circular(999),
                          border: Border.all(
                            color: _isStreaming ? AppColors.statusOk : AppColors.darkBorder,
                          ),
                        ),
                        child: Text(
                          _connectionStatus,
                          style: AppTypography.body(
                            _isStreaming ? AppColors.statusOk : AppColors.darkTextSecondary,
                            size: AppTypography.textXs,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.space4),

              // Info Kamera & Server
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
                    _buildInfoRow('Lokasi Ruangan', _roomId),
                    const Divider(color: AppColors.darkBorder),
                    _buildInfoRow('Server Tujuan', _serverUrl),
                    const Divider(color: AppColors.darkBorder),
                    _buildInfoRow('Wake Lock', _isStreaming ? 'Aktif (Layar Tidak Tidur)' : 'Nonaktif'),
                    const Divider(color: AppColors.darkBorder),
                    _buildInfoRow('Foreground Service', 'Aktif (Tipe Camera - Android 14)'),
                  ],
                ),
              ),
              const Spacer(),

              // Tombol Mode Layar Gelap (OLED Saver)
              OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppColors.darkText,
                  side: const BorderSide(color: AppColors.darkBorder),
                  padding: const EdgeInsets.symmetric(vertical: AppSpacing.space4),
                  shape: const RoundedRectangleBorder(borderRadius: AppRadius.borderSm),
                ),
                icon: const Icon(Icons.dark_mode_outlined),
                label: Text(
                  'GELAPKAN LAYAR (HEMAT BATERAI OLED)',
                  style: AppTypography.body(AppColors.darkText, size: AppTypography.textSm, weight: FontWeight.w600),
                ),
                onPressed: () => setState(() => _isDimmedMode = true),
              ),
              const SizedBox(height: AppSpacing.space2),

              // Tombol Mulai / Berhenti Penyiaran
              SizedBox(
                height: 52,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _isStreaming ? AppColors.statusDanger : AppColors.darkAccent,
                    foregroundColor: AppColors.darkSurface,
                    shape: const RoundedRectangleBorder(borderRadius: AppRadius.borderSm),
                  ),
                  onPressed: _toggleStreaming,
                  child: Text(
                    _isStreaming ? 'HENTIKAN PENYIARAN KAMERA' : 'MULAI PENYIARAN KAMERA',
                    style: AppTypography.body(AppColors.darkSurface, size: AppTypography.textSm, weight: FontWeight.w600),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: AppTypography.body(AppColors.darkTextSecondary, size: AppTypography.textXs)),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.right,
              style: AppTypography.body(AppColors.darkText, size: AppTypography.textXs),
            ),
          ),
        ],
      ),
    );
  }
}
