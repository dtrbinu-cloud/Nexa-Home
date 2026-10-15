// test/fixtures/test_fixtures.dart
// Fixture data khusus untuk pengujian golden dan widget test di folder test/

class TestFixtures {
  static const List<Map<String, dynamic>> devices = [
    {
      'id': 'dev_lamp_1',
      'name': 'Lampu Utama',
      'room': 'Ruang Tamu',
      'is_online': true,
      'firmware_version': '1.0.4',
      'wifi_rssi': -58,
      'channels': [
        {
          'channel_key': 'relay_1',
          'channel_type': 'light',
          'name': 'Lampu Utama',
          'current_value': 'true',
        }
      ],
    },
    {
      'id': 'dev_fan_1',
      'name': 'Kipas Plafon',
      'room': 'Kamar Depan',
      'is_online': true,
      'firmware_version': '1.0.2',
      'wifi_rssi': -65,
      'channels': [
        {
          'channel_key': 'relay_2',
          'channel_type': 'fan',
          'name': 'Kipas Plafon',
          'current_value': 'false',
        }
      ],
    },
    {
      'id': 'dev_sensor_mq2',
      'name': 'Sensor Gas MQ-2',
      'room': 'Dapur',
      'is_online': true,
      'firmware_version': '1.1.0',
      'wifi_rssi': -70,
      'channels': [
        {
          'channel_key': 'mq2',
          'channel_type': 'gas_sensor',
          'name': 'Gas MQ-2',
          'current_value': '412',
        }
      ],
    },
    {
      'id': 'dev_sensor_ldr',
      'name': 'Sensor Cahaya LDR',
      'room': 'Teras',
      'is_online': true,
      'firmware_version': '1.0.1',
      'wifi_rssi': -62,
      'channels': [
        {
          'channel_key': 'ldr',
          'channel_type': 'light_sensor',
          'name': 'Cahaya Teras',
          'current_value': 'terang',
        }
      ],
    },
    {
      'id': 'dev_siren_1',
      'name': 'Sirine Alarm',
      'room': 'Koridor',
      'is_online': true,
      'firmware_version': '1.0.0',
      'wifi_rssi': -72,
      'channels': [
        {
          'channel_key': 'alarm_1',
          'channel_type': 'alarm',
          'name': 'Sirine',
          'current_value': 'false',
        }
      ],
    },
    {
      'id': 'dev_lamp_outdoor',
      'name': 'Lampu Taman',
      'room': 'Halaman',
      'is_online': false,
      'firmware_version': '1.0.0',
      'wifi_rssi': null,
      'channels': [
        {
          'channel_key': 'relay_out',
          'channel_type': 'light',
          'name': 'Lampu Taman',
          'current_value': 'false',
        }
      ],
    },
  ];

  static const List<Map<String, dynamic>> cameras = [
    {
      'id': 'cam_1',
      'name': 'Halaman Depan',
      'location': 'Luar Rumah',
      'is_online': true,
      'privacy_mode': false,
      'last_seen': 'Baru saja',
    },
    {
      'id': 'cam_2',
      'name': 'Ruang Tamu',
      'location': 'Dalam Rumah',
      'is_online': true,
      'privacy_mode': true,
      'last_seen': 'Baru saja',
    },
  ];

  static const List<Map<String, dynamic>> members = [
    {
      'id': 'usr_1',
      'username': 'admin',
      'role': 'Admin',
      'is_active': true,
      'last_active': 'Hari ini, 18:30',
    },
    {
      'id': 'usr_2',
      'username': 'anggota1',
      'role': 'Anggota',
      'is_active': true,
      'last_active': 'Hari ini, 17:15',
    },
    {
      'id': 'usr_3',
      'username': 'anak1',
      'role': 'Anak',
      'is_active': true,
      'last_active': 'Kemarin, 21:00',
    },
  ];

  static const List<Map<String, dynamic>> notifications = [
    {
      'id': 'notif_1',
      'type': 'gas',
      'severity': 'danger',
      'title': 'Gas Terdeteksi',
      'description': 'Kadar gas di Dapur melebihi ambang batas aman.',
      'timestamp': 'Hari ini, 14:32',
      'created_at': '2026-10-14T14:32:00Z',
    },
    {
      'id': 'notif_2',
      'type': 'device_offline',
      'severity': 'warn',
      'title': 'Perangkat Offline',
      'description': 'Lampu Taman tidak merespons koneksi hub.',
      'timestamp': 'Hari ini, 11:05',
      'created_at': '2026-10-14T11:05:00Z',
    },
    {
      'id': 'notif_3',
      'type': 'motion',
      'severity': 'ok',
      'title': 'Gerakan Terdeteksi',
      'description': 'Kamera Halaman Depan mendeteksi pergerakan.',
      'timestamp': 'Kemarin, 22:15',
      'created_at': '2026-10-13T22:15:00Z',
    },
  ];

  static const Map<String, dynamic> familySummary = {
    'study_time_hours': 3.5,
    'late_night_active': false,
    'fall_events_count': 0,
    'last_seen_zone': 'Ruang Belajar',
  };
}
