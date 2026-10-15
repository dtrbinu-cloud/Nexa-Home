import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:app/screens/all_devices_screen.dart';
import 'package:app/screens/settings_screen.dart';
import 'package:app/screens/tabs/assistant_tab.dart';
import 'package:app/screens/tabs/home_tab.dart';
import 'package:app/theme/tokens.dart';

void main() {
  Widget buildScaledApp({
    required Widget child,
    required Size size,
    required Brightness brightness,
    double textScale = 1.3,
  }) {
    return ProviderScope(
      child: MediaQuery(
        data: MediaQueryData(
          size: size,
          textScaler: TextScaler.linear(textScale),
        ),
        child: MaterialApp(
          theme: brightness == Brightness.dark ? AppTheme.dark() : AppTheme.light(),
          home: child,
        ),
      ),
    );
  }

  group('Pemeriksaan Bebas Overflow & Teks 130%', () {
    const sizes = [
      Size(360, 800),
      Size(412, 915),
    ];

    for (final size in sizes) {
      testWidgets('Beranda pada ${size.width.toInt()}x${size.height.toInt()} teks 130% bebas overflow', (tester) async {
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1.0;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        await tester.pumpWidget(buildScaledApp(
          child: const HomeTab(),
          size: size,
          brightness: Brightness.light,
        ));
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 300));

        expect(tester.takeException(), isNull, reason: 'Beranda tidak boleh melempar exception atau RenderFlex overflow');
      });

      testWidgets('Semua Perangkat pada ${size.width.toInt()}x${size.height.toInt()} teks 130% bebas overflow', (tester) async {
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1.0;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        await tester.pumpWidget(buildScaledApp(
          child: const AllDevicesScreen(),
          size: size,
          brightness: Brightness.light,
        ));
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 300));

        expect(tester.takeException(), isNull, reason: 'Semua Perangkat tidak boleh melempar exception atau RenderFlex overflow');
      });

      testWidgets('Asisten pada ${size.width.toInt()}x${size.height.toInt()} teks 130% bebas overflow', (tester) async {
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1.0;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        await tester.pumpWidget(buildScaledApp(
          child: const AssistantTab(),
          size: size,
          brightness: Brightness.light,
        ));
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 300));

        expect(tester.takeException(), isNull, reason: 'Asisten tidak boleh melempar exception atau RenderFlex overflow');
      });

      testWidgets('Pengaturan pada ${size.width.toInt()}x${size.height.toInt()} teks 130% bebas overflow', (tester) async {
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1.0;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        await tester.pumpWidget(buildScaledApp(
          child: const SettingsScreen(),
          size: size,
          brightness: Brightness.light,
        ));
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 300));

        expect(tester.takeException(), isNull, reason: 'Pengaturan tidak boleh melempar exception atau RenderFlex overflow');
      });
    }
  });
}
