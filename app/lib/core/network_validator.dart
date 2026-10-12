/// Validasi keamanan alamat server untuk aplikasi Rumah.
/// Mencegah pengiriman kredensial HTTP tanpa enkripsi ke internet publik.
class NetworkValidator {
  static const Set<String> _loopbackHosts = {
    'localhost',
    '127.0.0.1',
    '10.0.2.2', // Android emulator host loopback
  };

  /// Memeriksa apakah IP string merupakan alamat privat RFC 1918
  static bool isPrivateIPv4(String host) {
    if (_loopbackHosts.contains(host.toLowerCase())) return true;

    final parts = host.split('.');
    if (parts.length != 4) return false;

    final octets = <int>[];
    for (final p in parts) {
      final n = int.tryParse(p);
      if (n == null || n < 0 || n > 255) return false;
      octets.add(n);
    }

    final o1 = octets[0];
    final o2 = octets[1];

    // 10.0.0.0/8
    if (o1 == 10) return true;

    // 172.16.0.0/12 (172.16.x.x s/d 172.31.x.x)
    if (o1 == 172 && o2 >= 16 && o2 <= 31) return true;

    // 192.168.0.0/16
    if (o1 == 192 && o2 == 168) return true;

    return false;
  }

  /// Memvalidasi URL server: jika HTTP, host WAJIB IP privat atau localhost.
  /// Jika bukan privat, WAJIB menggunakan HTTPS.
  static String? validateServerUrl(String rawUrl) {
    final trimmed = rawUrl.trim();
    if (trimmed.isEmpty) {
      return 'Alamat server tidak boleh kosong.';
    }

    Uri? uri;
    try {
      uri = Uri.parse(trimmed);
    } catch (_) {
      return 'Format alamat server tidak valid.';
    }

    if (!uri.hasScheme || (uri.scheme != 'http' && uri.scheme != 'https')) {
      return 'Skema protokol harus diawali dengan http:// atau https://';
    }

    final host = uri.host;
    if (host.isEmpty) {
      return 'Host server tidak valid.';
    }

    if (uri.scheme == 'http') {
      if (!isPrivateIPv4(host)) {
        return 'Koneksi HTTP hanya diizinkan untuk IP privat lokal (192.168.x, 10.x, 172.16-31.x, localhost). Alamat publik wajib memakai https://';
      }
    }

    return null; // Valid
  }
}
