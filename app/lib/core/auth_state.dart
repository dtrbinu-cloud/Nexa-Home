import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:app/core/api_client.dart';
import 'package:app/core/storage.dart';

enum AuthStatus {
  initial,
  needsSetup,
  unauthenticated,
  twoFactorPending,
  authenticated,
}

class AuthState {
  final AuthStatus status;
  final String? username;
  final String? role;
  final String? tempToken;
  final String? errorMessage;
  final bool isLoading;

  const AuthState({
    required this.status,
    this.username,
    this.role,
    this.tempToken,
    this.errorMessage,
    this.isLoading = false,
  });

  AuthState copyWith({
    AuthStatus? status,
    String? username,
    String? role,
    String? tempToken,
    String? errorMessage,
    bool? isLoading,
  }) {
    return AuthState(
      status: status ?? this.status,
      username: username ?? this.username,
      role: role ?? this.role,
      tempToken: tempToken ?? this.tempToken,
      errorMessage: errorMessage,
      isLoading: isLoading ?? this.isLoading,
    );
  }
}

class AuthNotifier extends Notifier<AuthState> {
  @override
  AuthState build() {
    Future.microtask(() => init());
    return const AuthState(status: AuthStatus.initial);
  }

  Future<void> init() async {
    state = state.copyWith(isLoading: true);
    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.get('/api/auth/setup-status');
      final isSetup = res.data['is_setup'] as bool? ?? false;

      if (!isSetup) {
        state = state.copyWith(status: AuthStatus.needsSetup, isLoading: false);
        return;
      }

      final token = await StorageService.getAccessToken();
      if (token != null && token.isNotEmpty) {
        try {
          final meRes = await dio.get('/api/auth/me');
          final user = meRes.data;
          state = AuthState(
            status: AuthStatus.authenticated,
            username: user['username'] as String?,
            role: user['role'] as String?,
            isLoading: false,
          );
          return;
        } catch (_) {
          await StorageService.clearAuth();
        }
      }

      state = state.copyWith(status: AuthStatus.unauthenticated, isLoading: false);
    } catch (_) {
      state = state.copyWith(
        status: AuthStatus.unauthenticated,
        errorMessage: 'Gagal terhubung ke server',
        isLoading: false,
      );
    }
  }

  Future<bool> setupAdmin({
    required String setupCode,
    required String username,
    required String password,
  }) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.post(
        '/api/auth/setup-admin',
        data: {
          'setup_code': setupCode.trim(),
          'username': username.trim(),
          'password': password,
        },
      );
      if (res.statusCode == 201) {
        state = state.copyWith(status: AuthStatus.unauthenticated, isLoading: false);
        return true;
      }
      return false;
    } on DioException catch (e) {
      String msg = 'Setup gagal';
      if (e.response?.data != null) {
        msg = e.response!.data['detail']?.toString() ?? msg;
      }
      state = state.copyWith(isLoading: false, errorMessage: msg);
      return false;
    } catch (_) {
      state = state.copyWith(isLoading: false, errorMessage: 'Terjadi kesalahan sistem.');
      return false;
    }
  }

  Future<bool> login(String username, String password) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.post(
        '/api/auth/login',
        data: {'username': username.trim(), 'password': password},
      );

      final data = res.data;
      if (data['status'] == '2fa_required') {
        state = state.copyWith(
          status: AuthStatus.twoFactorPending,
          username: username.trim(),
          tempToken: data['temp_token'] as String?,
          isLoading: false,
        );
        return true;
      }

      final access = data['access_token'] as String;
      final refresh = data['refresh_token'] as String;
      final role = data['user']['role'] as String;

      await StorageService.setAccessToken(access);
      await StorageService.setRefreshToken(refresh);
      await StorageService.setUsername(username.trim());
      await StorageService.setRole(role);

      state = AuthState(
        status: AuthStatus.authenticated,
        username: username.trim(),
        role: role,
        isLoading: false,
      );
      return true;
    } on DioException catch (e) {
      String msg = 'Login gagal';
      if (e.response?.data != null) {
        msg = e.response!.data['detail']?.toString() ?? msg;
      }
      state = state.copyWith(isLoading: false, errorMessage: msg);
      return false;
    } catch (_) {
      state = state.copyWith(isLoading: false, errorMessage: 'Koneksi ke server gagal.');
      return false;
    }
  }

  Future<bool> verify2FA(String code) async {
    if (state.tempToken == null) return false;
    state = state.copyWith(isLoading: true, errorMessage: null);

    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.post(
        '/api/auth/verify-2fa',
        data: {
          'temp_token': state.tempToken,
          'code': code.trim(),
        },
      );

      final data = res.data;
      final access = data['access_token'] as String;
      final refresh = data['refresh_token'] as String;
      final role = data['user']['role'] as String;
      final user = data['user']['username'] as String;

      await StorageService.setAccessToken(access);
      await StorageService.setRefreshToken(refresh);
      await StorageService.setUsername(user);
      await StorageService.setRole(role);

      state = AuthState(
        status: AuthStatus.authenticated,
        username: user,
        role: role,
        isLoading: false,
      );
      return true;
    } on DioException catch (e) {
      String msg = 'Verifikasi 2FA gagal';
      if (e.response?.data != null) {
        msg = e.response!.data['detail']?.toString() ?? msg;
      }
      state = state.copyWith(isLoading: false, errorMessage: msg);
      return false;
    } catch (_) {
      state = state.copyWith(isLoading: false, errorMessage: 'Terjadi kesalahan sistem.');
      return false;
    }
  }

  Future<void> logout() async {
    await StorageService.clearAuth();
    state = const AuthState(status: AuthStatus.unauthenticated);
  }
}

final authProvider = NotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

class ThemeModeNotifier extends Notifier<String> {
  @override
  String build() {
    Future.microtask(() async {
      final mode = await StorageService.getThemeMode();
      state = mode;
    });
    return 'light';
  }

  Future<void> toggle() async {
    final next = state == 'light' ? 'dark' : 'light';
    state = next;
    await StorageService.setThemeMode(next);
  }

  Future<void> setMode(String mode) async {
    state = mode;
    await StorageService.setThemeMode(mode);
  }
}

final themeModeProvider = NotifierProvider<ThemeModeNotifier, String>(ThemeModeNotifier.new);
