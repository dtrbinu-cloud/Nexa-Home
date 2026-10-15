import 'package:dio/dio.dart';

class CameraApiClient {
  static final Dio _dio = Dio(
    BaseOptions(
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
      headers: {'Content-Type': 'application/json'},
    ),
  );

  static Future<Map<String, dynamic>> pairCamera({
    required String serverUrl,
    required String pairingCode,
  }) async {
    final cleanUrl = serverUrl.replaceAll(RegExp(r'/+$'), '');
    final endpoint = '$cleanUrl/api/cameras/pair';

    try {
      final response = await _dio.post(
        endpoint,
        data: {'pairing_code': pairingCode.trim()},
      );

      if (response.statusCode == 200 && response.data is Map<String, dynamic>) {
        return response.data as Map<String, dynamic>;
      } else {
        throw Exception('Gagal memasangkan kamera: Respons tidak valid dari server.');
      }
    } on DioException catch (e) {
      final detail = e.response?.data is Map ? e.response?.data['detail'] : e.message;
      throw Exception('Gagal memasangkan kamera: ${detail ?? "Tidak dapat terhubung ke server"}');
    }
  }
}
