import 'package:flutter_test/flutter_test.dart';
import 'package:camera_app/main.dart';

void main() {
  testWidgets('CameraApp menampilkan PairingScreen saat belum dipasangkan', (WidgetTester tester) async {
    await tester.pumpWidget(const CameraApp(isPaired: false));
    await tester.pumpAndSettle();

    expect(find.text('Pairing Kamera HP'), findsOneWidget);
    expect(find.text('Alamat Server LAN'), findsOneWidget);
    expect(find.text('Kode Pairing Sekali Pakai'), findsOneWidget);
    expect(find.text('PASANGKAN KAMERA SEKARANG'), findsOneWidget);
  });

  testWidgets('CameraApp menampilkan CameraLiveScreen saat sudah dipasangkan', (WidgetTester tester) async {
    await tester.pumpWidget(const CameraApp(isPaired: true));
    await tester.pump();

    expect(find.text('KAMERA AKTIF MEMANCARKAN STREAM'), findsOneWidget);
    expect(find.text('HENTIKAN PENYIARAN KAMERA'), findsOneWidget);
  });
}
