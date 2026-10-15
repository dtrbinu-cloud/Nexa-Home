import 'package:flutter_test/flutter_test.dart';
import 'package:app/core/network_validator.dart';

void main() {
  group('NetworkValidator Tests', () {
    test('Mengizinkan localhost dan emulator loopback lewat HTTP', () {
      expect(NetworkValidator.validateServerUrl('http://localhost:8000'), isNull);
      expect(NetworkValidator.validateServerUrl('http://127.0.0.1:8000'), isNull);
      expect(NetworkValidator.validateServerUrl('http://10.0.2.2:8000'), isNull);
    });

    test('Mengizinkan alamat LAN privat RFC 1918 lewat HTTP', () {
      // 192.168.0.0/16
      expect(NetworkValidator.validateServerUrl('http://192.168.1.100:8000'), isNull);
      expect(NetworkValidator.validateServerUrl('http://192.168.0.1:8000'), isNull);

      // 10.0.0.0/8
      expect(NetworkValidator.validateServerUrl('http://10.10.1.5:8000'), isNull);
      expect(NetworkValidator.validateServerUrl('http://10.254.0.1'), isNull);

      // 172.16.0.0/12 (172.16.x s/d 172.31.x)
      expect(NetworkValidator.validateServerUrl('http://172.16.0.1:8000'), isNull);
      expect(NetworkValidator.validateServerUrl('http://172.20.10.2:8000'), isNull);
      expect(NetworkValidator.validateServerUrl('http://172.31.255.254:8000'), isNull);
    });

    test('Menolak alamat publik atau domain internet bila menggunakan HTTP biasa', () {
      // IP Publik lewat HTTP ditolak
      final errPublicIp = NetworkValidator.validateServerUrl('http://8.8.8.8:8000');
      expect(errPublicIp, isNotNull);
      expect(errPublicIp, contains('Koneksi HTTP hanya diizinkan untuk IP privat lokal'));

      // Domain publik lewat HTTP ditolak
      final errDomain = NetworkValidator.validateServerUrl('http://smarthome.myfamily.com:8000');
      expect(errDomain, isNotNull);
      expect(errDomain, contains('Koneksi HTTP hanya diizinkan untuk IP privat lokal'));

      // 172 di luar rentang privat ditolak
      final err172 = NetworkValidator.validateServerUrl('http://172.32.0.1:8000');
      expect(err172, isNotNull);
    });

    test('Mengizinkan semua alamat jika menggunakan HTTPS aman', () {
      expect(NetworkValidator.validateServerUrl('https://smarthome.myfamily.com'), isNull);
      expect(NetworkValidator.validateServerUrl('https://8.8.8.8:8443'), isNull);
      expect(NetworkValidator.validateServerUrl('https://192.168.1.100:8443'), isNull);
    });

    test('Menolak URL kosong atau tanpa skema protokol', () {
      expect(NetworkValidator.validateServerUrl(''), isNotNull);
      expect(NetworkValidator.validateServerUrl('192.168.1.100:8000'), isNotNull);
      expect(NetworkValidator.validateServerUrl('ftp://192.168.1.100'), isNotNull);
    });
  });
}
