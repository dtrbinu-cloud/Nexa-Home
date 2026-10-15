import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:app/components/assistant_listening_sheet.dart';
import 'package:app/screens/add_camera_screen.dart';
import 'package:app/screens/add_device/choose_type_screen.dart';
import 'package:app/screens/add_device/esp32_error_screen.dart';
import 'package:app/screens/add_device/esp32_qr_scan_screen.dart';
import 'package:app/screens/add_device/esp32_step1_code_screen.dart';
import 'package:app/screens/add_device/esp32_step2_connect_wifi_screen.dart';
import 'package:app/screens/add_device/esp32_step3_wifi_setup_screen.dart';
import 'package:app/screens/add_device/esp32_step4_connecting_screen.dart';
import 'package:app/screens/add_device/esp32_success_screen.dart';
import 'package:app/screens/all_devices_screen.dart';
import 'package:app/screens/camera_live_screen.dart';
import 'package:app/screens/device_detail_screen.dart';
import 'package:app/screens/family_event_detail_screen.dart';
import 'package:app/screens/family_summary_screen.dart';
import 'package:app/screens/login_screen.dart';
import 'package:app/screens/manage_members_screen.dart';
import 'package:app/screens/notifications_screen.dart';
import 'package:app/screens/recording_player_screen.dart';
import 'package:app/screens/settings_screen.dart';
import 'package:app/screens/shell_screen.dart';
import 'package:app/screens/tabs/assistant_tab.dart';
import 'package:app/screens/tabs/home_tab.dart';
import 'package:app/screens/verify_2fa_screen.dart';
import 'package:app/theme/tokens.dart';

import 'package:flutter/services.dart';

void main() {
  setUpAll(() async {
    TestWidgetsFlutterBinding.ensureInitialized();

    final secureStorageMemory = <String, String>{
      'server_url': 'http://127.0.0.1:8000',
      'theme_mode': 'light',
      'access_token': 'test_token',
      'saved_username': 'admin',
      'saved_role': 'Admin',
    };

    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(
      const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'),
      (MethodCall methodCall) async {
        final args = methodCall.arguments;
        if (methodCall.method == 'read') {
          final key = args is Map ? args['key']?.toString() : null;
          return key != null ? secureStorageMemory[key] : null;
        }
        if (methodCall.method == 'write') {
          if (args is Map && args['key'] != null) {
            secureStorageMemory[args['key'].toString()] = args['value']?.toString() ?? '';
          }
          return null;
        }
        if (methodCall.method == 'containsKey') {
          final key = args is Map ? args['key']?.toString() : null;
          return key != null && secureStorageMemory.containsKey(key);
        }
        if (methodCall.method == 'readAll') {
          return secureStorageMemory;
        }
        if (methodCall.method == 'delete') {
          final key = args is Map ? args['key']?.toString() : null;
          if (key != null) secureStorageMemory.remove(key);
          return null;
        }
        return null;
      },
    );

    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(
      const MethodChannel('FlutterWebRTC.Event'),
      (MethodCall call) async => null,
    );
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(
      const MethodChannel('FlutterWebRTC.Method'),
      (MethodCall call) async => null,
    );
  });
  Widget buildTestApp({
    required Widget child,
    required Size size,
    required Brightness brightness,
  }) {
    return ProviderScope(
      child: MediaQuery(
        data: MediaQueryData(
          size: size,
          padding: const EdgeInsets.only(top: 24.0, bottom: 16.0),
        ),
        child: MaterialApp(
          debugShowCheckedModeBanner: false,
          theme: brightness == Brightness.dark ? AppTheme.dark() : AppTheme.light(),
          home: child,
        ),
      ),
    );
  }

  Future<void> renderAndMatch({
    required WidgetTester tester,
    required Widget widget,
    required String fileName,
    required Size size,
    required Brightness brightness,
  }) async {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(buildTestApp(
      child: widget,
      size: size,
      brightness: brightness,
    ));

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    await expectLater(
      find.byType(MaterialApp),
      matchesGoldenFile('../../docs/ui-review/mobile/$fileName'),
    );
  }

  group('Golden Tests 27 Layar Stitch - 360x800 & 412x915', () {
    const size360 = Size(360, 800);
    const size412 = Size(412, 915);

    // 1. Login
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('01 Login - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const LoginScreen(),
          fileName: 'screen_01_login_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 2. Kode Verifikasi 2FA
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('02 Verifikasi 2FA - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const Verify2FAScreen(),
          fileName: 'screen_02_verify_2fa_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 3. Beranda (360 + 412)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('03 Beranda - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const ShellScreen(initialTab: 0),
          fileName: 'screen_03_beranda_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
      testWidgets('03 Beranda - $suffix 412', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const ShellScreen(initialTab: 0),
          fileName: 'screen_03_beranda_${suffix}_412.png',
          size: size412,
          brightness: b,
        );
      });
    }

    // 4. Beranda Bahaya (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('04 Beranda Bahaya - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const Scaffold(body: HomeTab(forceDanger: true)),
          fileName: 'screen_04_beranda_bahaya_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 5. Semua Perangkat (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('05 Semua Perangkat - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const AllDevicesScreen(),
          fileName: 'screen_05_semua_perangkat_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 6. Detail Perangkat (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('06 Detail Perangkat - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const DeviceDetailScreen(deviceId: 'dev_lamp_1'),
          fileName: 'screen_06_detail_perangkat_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 7. Pilih Jenis Perangkat (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('07 Pilih Jenis - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const ChooseDeviceTypeScreen(),
          fileName: 'screen_07_pilih_jenis_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 8. Langkah 1 Kode Pairing (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('08 Langkah 1 Kode - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const Esp32Step1CodeScreen(),
          fileName: 'screen_08_langkah_1_kode_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 9. Langkah 2 Sambung WiFi Alat (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('09 Langkah 2 Sambung WiFi - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const Esp32Step2ConnectWifiScreen(),
          fileName: 'screen_09_langkah_2_wifi_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 10. Scan QR (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('10 Scan QR - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const Esp32QrScanScreen(),
          fileName: 'screen_10_scan_qr_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 11. Setup WiFi Rumah (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('11 Setup WiFi - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const Esp32Step3WifiSetupScreen(),
          fileName: 'screen_11_setup_wifi_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 12. Langkah 4 Menghubungkan (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('12 Langkah 4 Menghubungkan - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const Esp32Step4ConnectingScreen(),
          fileName: 'screen_12_langkah_4_menghubungkan_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 13. Berhasil Tambah Perangkat (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('13 Berhasil - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const Esp32SuccessScreen(),
          fileName: 'screen_13_berhasil_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 14. Gagal Tambah Perangkat (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('14 Gagal - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const Esp32ErrorScreen(
            variant: Esp32ErrorVariant.wrongPassword,
          ),
          fileName: 'screen_14_gagal_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 15. Asisten (360 + 412)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('15 Asisten - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const ShellScreen(initialTab: 2),
          fileName: 'screen_15_asisten_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
      testWidgets('15 Asisten - $suffix 412', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const ShellScreen(initialTab: 2),
          fileName: 'screen_15_asisten_${suffix}_412.png',
          size: size412,
          brightness: b,
        );
      });
    }

    // 16. Asisten Mendengarkan Sheet (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('16 Asisten Mendengarkan - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: Scaffold(
            body: Stack(
              children: [
                const AssistantTab(),
                Container(color: Colors.black38),
                Align(
                  alignment: Alignment.bottomCenter,
                  child: AssistantListeningSheet(
                    onTranscriptComplete: (_) {},
                  ),
                ),
              ],
            ),
          ),
          fileName: 'screen_16_asisten_mendengarkan_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 17. Kamera (360 + 412)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('17 Kamera - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const ShellScreen(initialTab: 1),
          fileName: 'screen_17_kamera_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
      testWidgets('17 Kamera - $suffix 412', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const ShellScreen(initialTab: 1),
          fileName: 'screen_17_kamera_${suffix}_412.png',
          size: size412,
          brightness: b,
        );
      });
    }

    // 18. Live View Kamera (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('18 Live View - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const CameraLiveScreen(
            cameraId: 'cam_1',
            cameraName: 'Halaman Depan',
          ),
          fileName: 'screen_18_live_view_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 19. Pemutar Rekaman (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('19 Pemutar Rekaman - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const RecordingPlayerScreen(
            recordingId: 'rec_1',
            cameraName: 'Halaman Depan',
          ),
          fileName: 'screen_19_pemutar_rekaman_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 20. Tambah Kamera (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('20 Tambah Kamera - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const AddCameraScreen(),
          fileName: 'screen_20_tambah_kamera_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 21. Keluarga Ringkasan (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('21 Keluarga Ringkasan - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const FamilySummaryScreen(),
          fileName: 'screen_21_keluarga_ringkasan_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 22. Detail Kejadian Keluarga (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('22 Detail Kejadian - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const FamilyEventDetailScreen(
            event: {
              'id': 'EV-8842',
              'title': 'Gerakan di Teras',
              'created_at': '2026-10-14T08:42:15',
              'camera_name': 'Teras Depan',
              'event_type': 'Gerakan',
            },
          ),
          fileName: 'screen_22_detail_kejadian_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 23. Lainnya (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('23 Lainnya - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const ShellScreen(initialTab: 3),
          fileName: 'screen_23_lainnya_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 24. Notifikasi (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('24 Notifikasi - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const NotificationsScreen(),
          fileName: 'screen_24_notifikasi_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 25. Pengaturan (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('25 Pengaturan - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const SettingsScreen(),
          fileName: 'screen_25_pengaturan_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 26. Kelola Anggota (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('26 Kelola Anggota - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const ManageMembersScreen(),
          fileName: 'screen_26_kelola_anggota_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }

    // 27. Shell Shared Bottom Nav (360)
    for (final b in [Brightness.light, Brightness.dark]) {
      final suffix = b == Brightness.dark ? 'dark' : 'light';
      testWidgets('27 Shell Shared - $suffix 360', (tester) async {
        await renderAndMatch(
          tester: tester,
          widget: const ShellScreen(initialTab: 0),
          fileName: 'screen_27_shell_bottom_nav_${suffix}_360.png',
          size: size360,
          brightness: b,
        );
      });
    }
  });
}
