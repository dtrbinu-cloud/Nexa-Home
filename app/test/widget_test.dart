import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_badge.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_switch.dart';
import 'package:app/components/empty_state.dart';
import 'package:app/screens/add_device_screen.dart';
import 'package:app/main.dart';

void main() {
  testWidgets('Komponen dasar AppButton merender dengan benar', (WidgetTester tester) async {
    bool clicked = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AppButton(
            label: 'Uji Tombol',
            onPressed: () => clicked = true,
          ),
        ),
      ),
    );

    expect(find.text('Uji Tombol'), findsOneWidget);
    await tester.tap(find.text('Uji Tombol'));
    expect(clicked, isTrue);
  });

  testWidgets('Komponen dasar AppBadge dan AppCard merender dengan benar', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: AppCard(
            child: AppBadge(label: 'ONLINE', variant: AppBadgeVariant.ok),
          ),
        ),
      ),
    );

    expect(find.text('ONLINE'), findsOneWidget);
  });

  testWidgets('Komponen dasar AppSwitch merespon ketukan', (WidgetTester tester) async {
    bool switchVal = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: StatefulBuilder(
            builder: (context, setState) {
              return AppSwitch(
                value: switchVal,
                onChanged: (v) => setState(() => switchVal = v),
              );
            },
          ),
        ),
      ),
    );

    await tester.tap(find.byType(AppSwitch));
    await tester.pumpAndSettle();
    expect(switchVal, isTrue);
  });

  testWidgets('Komponen EmptyState menampilkan teks dan ikon', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: EmptyState(
            icon: Icon(PhosphorIcons.house()),
            title: 'Judul Kosong',
            description: 'Deskripsi keadaan kosong',
          ),
        ),
      ),
    );

    expect(find.text('Judul Kosong'), findsOneWidget);
    expect(find.text('Deskripsi keadaan kosong'), findsOneWidget);
  });

  testWidgets('Aplikasi utama RumahApp dapat di-mount', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: RumahApp(),
      ),
    );

    await tester.pump();
    expect(find.byType(RumahApp), findsOneWidget);
  });

  testWidgets('Layar AddDeviceScreen merender form input', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          home: AddDeviceScreen(),
        ),
      ),
    );

    await tester.pump();
    expect(find.text('Tambah Perangkat'), findsOneWidget);
    expect(find.text('Daftarkan Perangkat'), findsOneWidget);
  });
}
