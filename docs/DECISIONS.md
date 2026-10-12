# Keputusan Arsitektur Sistem Smart Home "Rumah"
Dokumen ini mencatat keputusan teknis awal (Tahap 0) untuk sistem smart home "Rumah".

---

## 1. Arsitektur Klien: Flutter Native Android (Utama) & Web React (Dibekukan)

### Pilihan
- **Klien Utama**: **Flutter Native Android** di folder `app/` untuk smartphone keluarga, dengan dukungan background sync, autentikasi biometrik lokal (`local_auth`), dan penyimpanan token terenkripsi (`flutter_secure_storage`).
- **Web Frontend**: Kode React di folder `web/` dibekukan (tidak ditambah fitur, tidak dihapus).
- **Single Source of Truth Desain**: `web/src/design-tokens.json` tetap menjadi sumber tunggal warna, font, dan ukuran untuk semua klien (dikonversi otomatis ke `app/lib/theme/tokens.dart`).

---

## 2. Broker Mosquitto & Keamanan Jaringan IoT

### Pilihan
- **Distribusi**: Binary Windows resmi Mosquitto (bukan Docker), dipasang dan dikonfigurasi sebagai Windows Service oleh `scripts/setup.ps1`. Unduhan diverifikasi dengan checksum SHA-256.
- **Batasan Jaringan**: Broker hanya mendengarkan pada jaringan LAN lokal (port 1883). Tidak diekspos ke internet.
- **Enkripsi TLS**: Enkripsi TLS/MQTTS ditunda ke **Tahap 7** setelah arsitektur lokal stabil.
- **Kredensial Unik Per Perangkat**:
  - Setiap perangkat memiliki username dan password MQTT acak unik yang dibuat saat didaftarkan oleh admin.
  - Backend menulis berkas password (`mosquitto_passwd`) dan ACL (`mosquitto.acl`) Mosquitto lalu me-reload broker.
  - Perangkat hanya berhak publish/subscribe ke prefix topiknya sendiri: `home/{device_id}/#`.
  - Backend server memiliki akun khusus dengan hak akses penuh ke seluruh topik `home/#`.

---

## 3. Skema Topik MQTT

Protokol MQTT menggantikan HTTP polling lama pada firmware ESP32 untuk latensi rendah, efisiensi bandwidth, dan deteksi putus koneksi instan via LWT (Last Will and Testament).

### Konvensi Topik
Root topik: `home/{device_id}/{channel_or_action}`
*(Catatan: Ruangan HANYA disimpan di database backend sebagai metadata, tidak masuk ke hierarki topik MQTT).*

| Topik | Arah | QoS | Retain | Deskripsi & Format Payload |
|---|---|---|---|---|
| `home/{device_id}/availability` | ESP → Broker | 1 | True | Status koneksi hardware. Payload: `"online"` atau `"offline"`. ESP memasang LWT payload `"offline"`. |
| `home/{device_id}/cmd` | Server → ESP | 1 | False | Perintah kontrol. Format JSON: `{"id": "cmd_uuid", "channel": "lamp_tengah", "action": "set", "value": true}` |
| `home/{device_id}/state` | ESP → Server | 1 | True | Laporan status channel dan sensor berkala atau setelah aksi. Format JSON: `{"channels": {"lamp_tengah": true, ...}, "sensors": {"gas_raw": 420, "is_dark": false}, "ts": 1718000000}` |
| `home/{device_id}/event` | ESP → Server | 2 | False | Kejadian darurat/spontan. Format JSON: `{"event": "gas_alarm", "channel": "mq2", "value": 1650, "threshold": 1500, "ts": 1718000000}` |

---

## 4. Firmware ESP32 Baru: C++ PlatformIO

### Pilihan
- Menggunakan C++ dengan PlatformIO (Arduino ESP32 Core) di folder `firmware/esp32/`.
- Firmware MicroPython lama di `firmware/legacy/` dibekukan dan tidak disentuh.
- Seluruh rahasia WiFi & MQTT diisolasi ke `secrets.h` (diabaikan oleh `.gitignore`, disediakan `secrets.h.example`).
- Konfigurasi pin terpusat di `config.h`. Loop utama non-blocking (memakai `millis()`), dilengkapi hardware watchdog (WDT) dan OTA update terproteksi password.
- Proteksi ADC ESP32: MQ2 output analog 5 V membutuhkan pembagi tegangan (*voltage divider*) 3.3 V sebelum masuk ke pin ADC 33.

---

## 3. Skema Database Awal (SQLite WAL)

Database menggunakan **SQLite 3** dengan mode **WAL (Write-Ahead Logging)** untuk konkurensi pembacaan tinggi tanpa memblokir penulisan event sensor.

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;
```

### Tabel Inti

#### `users`
Menyimpan akun pengguna sistem.
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `username` (VARCHAR(50) UNIQUE NOT NULL)
- `password_hash` (VARCHAR(255) NOT NULL) -- Argon2id
- `role` (VARCHAR(20) NOT NULL) -- 'admin' (orang tua), 'member', 'child'
- `totp_secret` (VARCHAR(64) NULL) -- 2FA untuk admin
- `is_active` (BOOLEAN DEFAULT 1)
- `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
- `updated_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

#### `audit_logs`
Mencatat aktivitas untuk keamanan dan transparansi keluarga.
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `user_id` (INTEGER NULL REFERENCES users(id))
- `action` (VARCHAR(100) NOT NULL) -- contoh: 'device.toggle', 'auth.login', 'camera.view'
- `target_type` (VARCHAR(50) NULL) -- 'device', 'channel', 'camera', 'system'
- `target_id` (VARCHAR(50) NULL)
- `details` (JSON/TEXT NULL)
- `ip_address` (VARCHAR(45) NULL)
- `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

#### `devices`
Registri fisik modul (ESP32, sensor node, kamera HP).
- `id` (VARCHAR(50) PRIMARY KEY) -- contoh: 'esp32_main', 'cam_ruang_tamu'
- `name` (VARCHAR(100) NOT NULL)
- `room` (VARCHAR(50) NOT NULL)
- `device_type` (VARCHAR(30) NOT NULL) -- 'esp32', 'camera_phone', 'sensor_hub'
- `is_online` (BOOLEAN DEFAULT 0)
- `last_seen_at` (TIMESTAMP NULL)
- `ip_address` (VARCHAR(45) NULL)
- `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

#### `channels`
Kanal input/output pada setiap perangkat (dapat ditambah tanpa ubah skema).
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `device_id` (VARCHAR(50) NOT NULL REFERENCES devices(id) ON DELETE CASCADE)
- `channel_key` (VARCHAR(50) NOT NULL) -- contoh: 'lamp_tengah', 'relay_fan', 'mq2', 'ldr'
- `name` (VARCHAR(100) NOT NULL)
- `channel_type` (VARCHAR(30) NOT NULL) -- 'switch', 'relay', 'gas_sensor', 'light_sensor', 'buzzer'
- `current_value` (TEXT NULL) -- 'true', 'false', '1420'
- `unit` (VARCHAR(20) NULL)
- `updated_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
- UNIQUE(device_id, channel_key)

#### `telemetry_logs`
Penyimpanan ringkas nilai sensor berkala (retensi otomatis).
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `device_id` (VARCHAR(50) NOT NULL)
- `channel_key` (VARCHAR(50) NOT NULL)
- `value_num` (REAL NULL)
- `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

#### `automations`
Aturan otomatisasi lokal (misal: jika LDR gelap dan orang terdeteksi, nyalakan lampu).
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `name` (VARCHAR(100) NOT NULL)
- `is_enabled` (BOOLEAN DEFAULT 1)
- `trigger_type` (VARCHAR(50) NOT NULL)
- `trigger_config` (JSON/TEXT NOT NULL)
- `action_config` (JSON/TEXT NOT NULL)
- `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

#### `cameras`
Pengaturan kamera HP dan retensi rekaman.
- `id` (VARCHAR(50) PRIMARY KEY)
- `name` (VARCHAR(100) NOT NULL)
- `room` (VARCHAR(50) NOT NULL)
- `token_hash` (VARCHAR(255) NOT NULL)
- `is_active` (BOOLEAN DEFAULT 1)
- `privacy_mode` (BOOLEAN DEFAULT 0)
- `retention_days` (INTEGER DEFAULT 7)
- `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

---

## 4. Strategi Runtime pada Hardware Target (i3 Gen 4, 8 GB RAM, Windows 10)

1. **Python Virtual Environment Terisolasi:** Menggunakan Python 3.11 (`py -3.11 -m venv .venv`).
2. **Asinkron & Non-Blocking:** Backend memakai FastAPI + asyncio, klien MQTT paho-mqtt di background worker thread/loop terpisah tanpa memblokir request HTTP/WebSocket.
3. **Manajemen Memori:**
   - Tidak ada proses Node.js di server saat mode produksi.
   - Database SQLite WAL menjaga pemakaian RAM tetap di bawah 20 MB.
   - Worker AI (tahap 5) dipisah prosesnya dan dijalankan hanya saat ada pemicu gerakan (motion trigger), bukan terus-menerus.
