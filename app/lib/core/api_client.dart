import 'package:dio/dio.dart';
import 'package:app/core/storage.dart';

class ApiClient {
  static Dio? _dio;

  static Future<Dio> getInstance() async {
    final serverUrl = await StorageService.getServerUrl();
    if (_dio == null || _dio!.options.baseUrl != serverUrl) {
      _dio = Dio(
        BaseOptions(
          baseUrl: serverUrl,
          connectTimeout: const Duration(seconds: 8),
          receiveTimeout: const Duration(seconds: 8),
          headers: {'Content-Type': 'application/json'},
        ),
      );

      _dio!.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) async {
            final token = await StorageService.getAccessToken();
            if (token != null && token.isNotEmpty) {
              options.headers['Authorization'] = 'Bearer $token';
            }
            return handler.next(options);
          },
          onError: (DioException error, handler) async {
            if (error.response?.statusCode == 401) {
              final refreshToken = await StorageService.getRefreshToken();
              if (refreshToken != null && error.requestOptions.path != '/api/auth/refresh') {
                try {
                  final refreshDio = Dio(BaseOptions(baseUrl: serverUrl));
                  final refreshRes = await refreshDio.post(
                    '/api/auth/refresh',
                    data: {'refresh_token': refreshToken},
                  );
                  if (refreshRes.statusCode == 200) {
                    final newAccess = refreshRes.data['access_token'] as String;
                    await StorageService.setAccessToken(newAccess);
                    final newRefresh = refreshRes.data['refresh_token'] as String?;
                    if (newRefresh != null && newRefresh.isNotEmpty) {
                      await StorageService.setRefreshToken(newRefresh);
                    }
                    error.requestOptions.headers['Authorization'] = 'Bearer $newAccess';
                    final retryRes = await _dio!.fetch(error.requestOptions);
                    return handler.resolve(retryRes);
                  }
                } catch (_) {
                  await StorageService.clearAuth();
                }
              }
            }
            return handler.next(error);
          },
        ),
      );
    }
    return _dio!;
  }

  static void reset() {
    _dio = null;
  }
}
