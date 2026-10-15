import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class CameraStorage {
  static const _storage = FlutterSecureStorage();

  static const _keyServerUrl = 'server_url';
  static const _keyCameraId = 'camera_id';
  static const _keyCameraToken = 'camera_token';
  static const _keyCameraName = 'camera_name';
  static const _keyRoomId = 'room_id';

  static Future<void> savePairingData({
    required String serverUrl,
    required String cameraId,
    required String cameraToken,
    required String cameraName,
    required String roomId,
  }) async {
    await _storage.write(key: _keyServerUrl, value: serverUrl);
    await _storage.write(key: _keyCameraId, value: cameraId);
    await _storage.write(key: _keyCameraToken, value: cameraToken);
    await _storage.write(key: _keyCameraName, value: cameraName);
    await _storage.write(key: _keyRoomId, value: roomId);
  }

  static Future<String?> getServerUrl() async => _storage.read(key: _keyServerUrl);
  static Future<String?> getCameraId() async => _storage.read(key: _keyCameraId);
  static Future<String?> getCameraToken() async => _storage.read(key: _keyCameraToken);
  static Future<String?> getCameraName() async => _storage.read(key: _keyCameraName);
  static Future<String?> getRoomId() async => _storage.read(key: _keyRoomId);

  static Future<bool> isPaired() async {
    final token = await getCameraToken();
    final url = await getServerUrl();
    return token != null && token.isNotEmpty && url != null && url.isNotEmpty;
  }

  static Future<void> clear() async {
    await _storage.deleteAll();
  }
}
