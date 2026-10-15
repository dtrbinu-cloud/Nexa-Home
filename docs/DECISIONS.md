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

## 4. Strategi Runtime pada Hardware Target (Diukur pada i7-1185G7, TIDAK DIUKUR pada i3 Gen 4)

1. **Python Virtual Environment Terisolasi:** Menggunakan Python 3.11 (`py -3.11 -m venv .venv`).
2. **Asinkron & Non-Blocking:** Backend memakai FastAPI + asyncio, klien MQTT paho-mqtt di background worker thread/loop terpisah tanpa memblokir request HTTP/WebSocket.
3. **Manajemen Memori:**
   - Tidak ada proses Node.js di server saat mode produksi.
   - Database SQLite WAL menjaga pemakaian RAM tetap di bawah 20 MB.
   - Worker AI (tahap 5) dipisah prosesnya dan dijalankan hanya saat ada pemicu gerakan (motion trigger), bukan terus-menerus.

---

## 5. Asisten Percakapan dan Suara (Tahap 3)

### 5.1 LLM: DeepSeek API
- **Sumber Dokumentasi Resmi**: [DeepSeek API Documentation](https://api-docs.deepseek.com/guides/function_calling) & [DeepSeek Quick Start](https://api-docs.deepseek.com/quick_start/pricing).
- **Nama Model**: `deepseek-chat` (DeepSeek-V3).
  - Model `deepseek-chat` mendukung percakapan interaktif dan *Tool Calling* (*Function Calling*) standar OpenAI-compatible.
  - Model `deepseek-reasoner` (DeepSeek-R1) tidak digunakan karena dokumentasi resmi menyatakan model reasoning tidak mendukung function calling.
  - Nama model diverifikasi saat startup; jika nama model di konfigurasi tidak valid, backend gagal (*fail-fast*) dengan pesan kesalahan jelas.
  - Seluruh kredensial (`DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`) HANYA tersimpan di `.env` server dan TIDAK PERNAH dikirim ke aplikasi klien.

### 5.2 TTS: Antarmuka TTSProvider & Fallback Otomatis
- **Antarmuka**: `TTSProvider` abstrak dengan dua implementasi:
  1. `EdgeTTSProvider` (Default): Menggunakan pustaka `edge-tts` Microsoft dengan suara Bahasa Indonesia: `id-ID-ArdiNeural` (pria) dan `id-ID-GadisNeural` (wanita).
  2. `PiperTTSProvider` (Offline): Menggunakan binary Piper dan model suara offline Bahasa Indonesia.
- **Failover Otomatis**: Jika request ke Edge TTS gagal (misal koneksi internet terputus, timeout, atau rate limit Microsoft), sistem otomatis beralih (*fallback*) ke Piper TTS lokal.
- **Audio Cache**: Kalimat-kalimat umum dan berulang di-cache di disk (`server/data/tts_cache/`) berbasis hash SHA-256 teks dan suara agar tidak menghabiskan bandwidth atau CPU.
- **Batas Panjang**: Endpoint TTS membatasi panjang input teks maksimum 500 karakter untuk mencegah penyalahgunaan beban CPU/jaringan.

### 5.3 STT: Pengenalan Suara Sisi Klien (Android)
- **Implementasi**: Speech-to-Text dijalankan secara native di aplikasi Flutter menggunakan paket `speech_to_text` (locale `id_ID`).
- **Tanpa STT Server**: Backend tidak memproses transkripsi audio suara di tahap ini, menghemat resource komputasi server lokal.
- **Catatan Privasi Pengaturan**: Pada menu Pengaturan dicantumkan catatan privasi resmi: *"Pada sebagian besar perangkat Android, pemrosesan pengenalan suara dilakukan oleh layanan suara Google."*

### 5.4 Function Calling & Keamanan Eksekusi
- **Prinsip Usulan (Proposal Only)**: LLM HANYA mengusulkan aksi melalui panggilan fungsi (*tool call*). LLM tidak memiliki akses eksekusi langsung ke broker MQTT atau database.
- **Verifikasi Izin Backend**: Backend memverifikasi identitas (`user_id`) dan peran (`role`) pengguna yang login sebelum mengeksekusi aksi apa pun yang diusulkan LLM.
- **Pembatasan Akun Anak (`child`)**:
  - Akun `child` hanya diizinkan mengontrol kanal yang secara eksplisit ditandai `allowed_for_child: true` oleh admin.
  - Akun `child` ditolak memicu aksi sensitif atau membaca data keluarga/item.
- **Konfirmasi Aksi Sensitif (Ya/Batal)**:
  - Kanal dapat ditandai `is_sensitive: true` oleh admin di database (contoh: saklar daya utama, pintu).
  - Perintah berdampak luas (seperti "matikan semua lampu" atau kontrol kanal sensitif) tidak langsung dieksekusi: backend mengembalikan objek penangguhan (*pending confirmation*) dan aplikasi menampilkan kartu konfirmasi Ya/Batal.
  - Konfirmasi hanya valid jika disetujui oleh pengguna yang sama yang meminta perintah. Konfirmasi oleh pengguna berbeda ditolak.
- **Parser Lokal (Fallback Aturan Sederhana)**:
  - Jika API DeepSeek tidak dapat dihubungi (offline atau kuota habis), backend otomatis menggunakan *rule-based parser* lokal berbasis ekspresi reguler untuk perintah umum (nyalakan/matikan kanal berdasarkan alias, tanya status).
  - Asisten secara eksplisit memberitahukan pengguna bahwa ia sedang beroperasi dalam mode darurat lokal terbatas.
- **Pencegahan Prompt Injection**:
  - Seluruh telemetry sensor, nama perangkat, dan hasil alat dibungkus sebagai data mentah dan diinstruksikan dalam `server/prompts/assistant.md` agar LLM tidak mengeksekusi instruksi di dalam data tersebut.
- **Pembatas Biaya & Anggaran**:
  - Rate limiting per pengguna per menit (`ASSISTANT_RATE_LIMIT_PER_MINUTE`).
  - Batas token per balasan (`ASSISTANT_MAX_TOKENS`).
  - Batas anggaran harian (`ASSISTANT_DAILY_BUDGET_CENTS`).

---

## 6. Kamera dari HP Bekas (Tahap 4)

### 6.1 Arsitektur Klien: Flutter Native Terpisah (`camera-app/`)
- Aplikasi kamera dibangun sebagai aplikasi Flutter native terpisah di direktori `camera-app/` (bukan PWA), memanfaatkan `flutter_webrtc` untuk penyiaran video efisien.
- Menjaga layar tetap aktif (*wake lock* via `wakelock_plus`), menjalankan Android Foreground Service (tipe `camera` sesuai regulasi Android 14), mode hemat daya OLED (layar digelapkan namun sensor kamera tetap aktif), dan auto-reconnect backoff saat WiFi berkedip.
- Jika pengujian pada perangkat fisik tertentu menunjukkan ketidakstabilan di latar belakang, fallback yang diusulkan adalah modul native Kotlin CameraX tanpa mengubah arsitektur server.

### 6.2 MediaMTX Server & Hook Autentikasi HTTP
- Server media menggunakan binary resmi Windows **MediaMTX** (bluenviron/mediamtx), diverifikasi checksum SHA-256 dan dipasang sebagai Windows Service melalui `scripts/setup.ps1`.
- Server media HANYA mendengarkan pada jaringan lokal (LAN).
- Autentikasi terpusat di backend melalui hook HTTP MediaMTX (`POST /api/cameras/auth/mediamtx`):
  - **Publish (Kamera HP)**: Wajib menyertakan token kamera yang valid. Token dicocokkan dengan hash di database.
  - **Read (Pengguna)**: Wajib menyertakan JWT pengguna yang valid dan memiliki izin terhadap kamera tersebut.
  - **Pencabutan Token Instan**: Saat admin mencabut kamera, token langsung ditandai `revoked` dan koneksi stream aktif diputus seketika.

### 6.3 Pembatasan Live View Penuh Hanya di LAN (Dalam Rumah)
- **Keputusan**: Live view video WebRTC/WHEP hanya dapat diakses saat pengguna terhubung ke jaringan LAN rumah. Akses dari luar rumah (remote via Cloudflare Tunnel) HANYA menyediakan gambar diam (*snapshot*) berkala.
- **Alasan Teknis**:
  1. *Batasan Cloudflare Tunnels*: Cloudflare Free Tier melarang relay lalu lintas video streaming bitrate tinggi terus-menerus (pelanggaran Ketentuan Layanan Bagian 2.8 mengenai bandwidth non-HTML/API) dan dapat menyebabkan pemutusan akun.
  2. *Beban Uplink Internet Rumah*: Bandwidth unggah (*upload speed*) koneksi internet rumahan sangat terbatas. Menyiarkan stream video mentah ke luar rumah dapat melumpuhkan koneksi internet seluruh keluarga, sedangkan pengiriman snapshot ringan sangat ramah bandwidth.

### 6.4 Audio Kamera Dimatikan Secara Default (Privacy First)
- Seluruh kamera baru yang terpasang memiliki mikrofon/audio dalam keadaan **MATI secara default**.
- Admin dapat mengaktifkan audio secara manual per kamera melalui pengaturan dengan dialog peringatan privasi eksplisit di antarmuka.

### 6.5 Rekaman Gerakan Terenkripsi AES-256-GCM
- Video hanya direkam saat terdeteksi gerakan, dengan *pre-roll* 3 detik sebelum gerakan dan *post-roll* 3 detik setelah gerakan selesai.
- Berkas rekaman dienkripsi menggunakan **AES-256-GCM** sebelum disimpan ke disk (`server/data/recordings/`).
- Kunci enkripsi simetris 256-bit diambil dari variabel lingkungan `.env` (`RECORDING_ENCRYPTION_KEY`) dan **TIDAK PERNAH disimpan di database**.
- Berkas di disk tidak dapat diputar langsung oleh pemutar media apa pun tanpa kunci enkripsi. Dekripsi dilakukan *on-the-fly* secara streaming hanya saat disajikan kepada admin atau pengguna berwenang.

### 6.6 Deteksi Gerakan Sisi Server & Retensi Otomatis
- Ekstraksi frame kecil (maks 2 FPS, lebar 320 px) dari stream internal MediaMTX via FFmpeg, diproses oleh OpenCV untuk mendeteksi kontur perbedaan frame (*frame difference*).
- Batas kamera aktif simultan untuk deteksi dibatasi config (default 3 kamera) demi menjaga beban CPU tetap efisien (diukur pada i7-1185G7, TIDAK DIUKUR pada i3).
- *Mode Privasi*: Menghentikan deteksi, perekaman, dan penyiaran video seketika saat diaktifkan (baik manual maupun terjadwal).
- *Retensi Disk Otomatis*: Membersihkan rekaman lebih tua dari batas hari (`RECORDING_RETENTION_DAYS`) dan memastikan total ukuran rekaman tidak melebihi ambang batas ruang penyimpanan.

---

## 7. Vision AI dan Pencarian Barang (Tahap 5)

### 7.1 Lisensi Model Ultralytics & Alternatif Permisif
- **Lisensi Ultralytics**: Model YOLO11 dari Ultralytics dirilis di bawah lisensi **AGPL-3.0**.
  - *Status Hukum*: **Aman untuk penggunaan pribadi di rumah sendiri**, karena tidak didistribusikan atau dijual sebagai layanan komersial/SaaS kepada publik.
  - *Batasan*: Jika sistem "Rumah" kelak didistribusikan kepada pihak ketiga atau dijual komersial, turunan kode yang berinteraksi dengan runtime AGPL harus di-open-source di bawah AGPL-3.0.
- **Alternatif Berlisensi Permisif**:
  - **RT-DETR (Real-Time Detection Transformer)** dari Baidu / Lyglkp: Berlisensi **Apache-2.0** (bebas dipakai komersial tanpa kewajiban copyleft).
  - **MobileNet-SSD v2 / YOLO-NAS**: Berlisensi **Apache-2.0**.
- **Isolasi Runtime**: Backend produksi **TIDAK MENGGUNAKAN** paket `ultralytics` sama sekali saat runtime. Model diekspor ke format ONNX satu kali menggunakan `scripts/export_models.py`, dan inferensi saat runtime 100% menggunakan `onnxruntime` murni.

### 7.2 Hasil Benchmark Model di Mesin Host (Host: Intel Core i7-1185G7 @ 3.00GHz, 2 Thread ONNX Runtime)
Benchmark dijalankan menggunakan `scripts/benchmark_models.py` pada 50 frame aktual:

| Model | Ukuran Input | Presisi | Latensi per Frame | Throughput Total | FPS per Kamera (3 Kamera) | RAM Alokasi | Lolos Target (≥ 2.0 FPS/cam) |
|---|---|---|---|---|---|---|---|
| YOLO11n | 480 px | FP32 | 55.02 ms | 18.18 FPS | 6.06 FPS/cam | 115.8 MB | YA |
| YOLO11n | 480 px | INT8 | 80.01 ms | 12.50 FPS | 4.17 FPS/cam | 109.5 MB | YA |
| **YOLO11n** | **640 px** | **FP32** | **95.69 ms** | **10.45 FPS** | **3.48 FPS/cam** | **153.7 MB** | **YA (DIPILIH)** |
| YOLO11n | 640 px | INT8 | 130.57 ms | 7.66 FPS | 2.55 FPS/cam | 139.8 MB | YA |
| YOLO11s | 480 px | FP32 | 137.84 ms | 7.25 FPS | 2.42 FPS/cam | 183.9 MB | YA |
| YOLO11s | 480 px | INT8 | 187.55 ms | 5.33 FPS | 1.78 FPS/cam | 157.0 MB | TIDAK |
| YOLO11s | 640 px | FP32 | 247.42 ms | 4.04 FPS | 1.35 FPS/cam | 255.2 MB | TIDAK |
| YOLO11s | 640 px | INT8 | 298.97 ms | 3.34 FPS | 1.11 FPS/cam | 209.6 MB | TIDAK |

#### Alasan Pemilihan `YOLO11n-640-FP32`:
1. **Target Frame Rate Terpenuhi**: Menghasilkan **3.48 FPS per kamera** pada beban 3 kamera aktif bersamaan (di atas batas syarat ≥ 2.0 FPS).
2. **Kebutuhan Resolusi Objek Kecil**: Resolusi 640 px sangat esensial untuk menemukan barang-barang kecil dalam rumah (misal: ponsel, cangkir, botol, remote tv). Pada resolusi 480 px, objek kecil kehilangan fitur visual dan tingkat deteksi menurun drastis.
3. **Anomali INT8 vs FP32 pada CPU**: Kuantisasi INT8 pada CPU ini ternyata 20–45% lebih lambat daripada FP32 (CPU host terbukti memiliki instruksi AVX-512 VNNI via CPUID, namun penyebab pasti mengapa INT8 lebih lambat di ONNX Runtime CPU EP tidak diselidiki secara mendalam; penyebab tidak diselidiki).
4. **Model Seri 's' Terlalu Berat**: Model YOLO11s (small) pada 640 px hanya mampu mencapai 1.35 FPS per kamera (di bawah batas minimum 2.0 FPS).

### 7.3 Daftar Checksum SHA-256 Model (Dihitung Lokal)
Dihitung langsung pada berkas biner di direktori `server/data/models/`:
- `server/data/models/yolo/yolo11n.onnx` (640 px FP32, 10,741,326 byte): `475bc604fa425a99f0185642c0a52b10dbc087035c022f75cbd3e31505c4670b`
- `server/data/models/yolo/yolo11n-pose.onnx` (640 px FP32, 11,853,353 byte): `a7add873d63faa4a0eaefc26a3bea09c6fce5836fa38fb54ae6db72438c5edf8`
- `server/data/models/yolo/yolo11n_480.onnx` (480 px FP32, 10,667,750 byte): `c35a166658e31874fa21be457279e4d7f6cff89e47826dc67075df16dddae845`
- `server/data/models/yolo/yolo11n_480_int8.onnx` (480 px INT8, 2,976,457 byte): `1f14e8c503c0473b577f77ad04f3d24370928db7b4cd5b7fb67c44ee7d26664c`
- `server/data/models/yolo/yolo11n_640_int8.onnx` (640 px INT8, 3,050,033 byte): `bb7534aa7f31c57d4051270595741eb8d98f3a6ae7edc32fc5bdf989b15e7b3b`
- `server/data/models/yolo/yolo11s_480.onnx` (480 px FP32, 37,978,142 byte): `5969f5c151d09742b987d7cca11b96138ff2b442a2ef755c789e5b1f2af379f9`
- `server/data/models/yolo/yolo11s_480_int8.onnx` (480 px INT8, 9,825,829 byte): `d4937846e0462d50d298c83f35f6e9ac00efb32d70a1595d85736a199057abfc`
- `server/data/models/yolo/yolo11s_640.onnx` (640 px FP32, 38,051,718 byte): `8c0af0da2d11b9c38e07e1adba55c3011eeb41c7f0751f30a3234a98dd2351b3`
- `server/data/models/yolo/yolo11s_640_int8.onnx` (640 px INT8, 9,899,405 byte): `4d5f9521e3107e0921396f59e28b5842372c26debcc1014820c497a8d0e6a8b2`
- `server/data/models/piper/id_ID-news_tts-medium.onnx` (62,950,044 byte): `ed8f02aa593f7af6b19acbdb8142e0da0dd72f46194eb33d38e0eb10a52597e8`
- `server/data/models/piper/id_ID-news_tts-medium.onnx.json` (5,050 byte): `1ef677072668a5e172e0759b1d3871f129009d1167f093325a17607f7add5ad7`

### 7.4 Privasi, Pelacakan Anonim & Keamanan Data
1. **Mode Privasi Kamera**: Ketika `privacy_mode` aktif pada suatu kamera, proses worker **SAMA SEKALI TIDAK MEMBUKA ATAU MEMBACA STREAM** kamera tersebut. Hal ini diverifikasi dalam unit test `test_vision_worker.py`.
2. **Pelacakan Orang Anonim**: Worker hanya mencatat kejadian kehadiran orang agregat `{kamera, waktu_mulai, waktu_selesai, jumlah_orang}`. Sistem **TIDAK MENYIMPAN GAMBAR WAJAH, TIDAK MENYIMPAN FOTO ORANG, DAN TIDAK MEMILIKI PENGENALAN IDENTITAS WAJAH**.
3. **Penyimpanan Thumbnail Benda Terenkripsi**: Thumbnail potongan gambar benda disimpan dalam keadaan terenkripsi simetris **AES-256-GCM** menggunakan kunci `RECORDING_ENCRYPTION_KEY`. Berkas thumbnail di disk tidak dapat dibaca oleh pembaca gambar biasa tanpa otentikasi backend.
4. **Deduplikasi Log Benda**: Benda yang berada di tempat yang sama tidak disimpan berulang-ulang setiap detik. Sistem memperbarui `last_seen_at` pada rekaman yang ada; kejadian baru hanya dibuat jika ada pergeseran posisi signifikan (IoU < 0.5) atau setelah jeda waktu tertentu.
5. **Kebijakan Akses Berbasis Peran (RBAC)**:
   - Pengguna `child` **DITOLAK SECARA MUTLAK** (HTTP 403) dari fitur pencarian barang dan akses thumbnail.
   - Pengguna `member` hanya dapat mencari dan melihat thumbnail dari kamera-kamera yang diizinkan untuknya.
   - Setiap permintaan akses dicatat dalam `audit_logs`.

### 7.5 Evaluasi Akurasi Vision AI (COCO val2017 Subset)
- **Sumber Anotasi & Gambar**: Dataset resmi COCO Consortium (Common Objects in Context), file anotasi `instances_val2017.json` (19.98 MB, md5: `46428e59f449448ff11e5a7d04d80a13`), diunduh langsung dari server resmi COCO (`http://images.cocodataset.org/annotations/annotations_trainval2017.zip` dan `http://images.cocodataset.org/val2017/`).
- **Lisensi Dataset**: Creative Commons Attribution 4.0 International License (CC BY 4.0). Gambar bersumber dari Flickr dengan lisensi penggunaan kreatif.
- **Kepatuhan Repositori (Git Cleanliness)**: Berkas citra dan anotasi COCO tidak dimasukkan ke dalam version control Git, melainkan diabaikan melalui `.gitignore` (`tests/data/coco_val2017_subset/` dan `tests/data/instances_val2017.json`) dan diunduh via skrip otomatis `scripts/download_coco_annotations.py` serta `scripts/prepare_coco_subset.py`.
- **Kriteria Pemilihan Subset Uji (Total 238 Gambar Unik)**:
  - 8 kelas barang target minimal 30 gambar per kelas: `cell phone` (40 GT), `remote` (47 GT), `bottle` (164 GT), `cup` (146 GT), `laptop` (39 GT), `book` (179 GT), `backpack` (50 GT), `handbag` (72 GT).
  - Kelas `person`: Menggunakan gambar di mana SEMUA orang dalam frame teranotasi lengkap (bukan gambar kerumunan/crowd `iscrowd == 0`), total 499 GT.
  - Kelas yang didukung dalam model namun tidak ada dalam subset uji ditandai secara jujur sebagai `TIDAK ADA DATA` (bukan 0% atau 100%, dan tidak diikutsertakan dalam perhitungan rata-rata agregat).
- **Pembatalan Hasil Uji Lama**: 65 frame berlabel sebelumnya yang berasal dari rekaman webcam laptop dibatalkan status validitasnya dan ditandai **TIDAK VALID** karena bounding box dibuat secara otomatis heuristik menggunakan model YOLO yang sama (self-referential/circular validation) dan file `webcam_record.mp4` telah dihapus permanen.

### 7.6 Manajemen Kunci Kriptografi & Privasi Data (.env)
- **Daftar Variabel Kunci di `.env`**:
  1. `SECRET_KEY`: Kunci simetris 256-bit untuk penandatanganan dan verifikasi JSON Web Token (JWT) pada sesi autentikasi pengguna web dan mobile.
  2. `MEDIA_ENCRYPTION_KEY`: Kunci enkripsi simetris master (AES-256-GCM) terpadu untuk mengenkripsi berkas rekaman video klip kamera (`.enc`) serta gambar thumbnail potongan objek (`.enc`) di disk. Kunci ini TIDAK PERNAH disimpan di database.
  3. `RECORDING_ENCRYPTION_KEY` & `CAMERA_ENCRYPTION_KEY`: Kunci lama yang dipertahankan di modul `encryption.py` sebagai *read fallback* mundur agar berkas-berkas terenkripsi lama tetap dapat didekripsi setelah server mengalami restart.
  4. `MEDIAMTX_AUTH_KEY`: Kunci token internal yang digunakan oleh proses AI Vision Worker untuk otentikasi stream MediaMTX tanpa memerlukan kredensial pengguna.
  5. `DEEPSEEK_API_KEY`: Kunci API cloud untuk integrasi asisten percakapan eksternal (opsional).
- **Jaminan Privasi Log Deteksi Benda**:
  - Kolom dan thumbnail potongan gambar untuk kelas `person` **DILARANG DAN TIDAK PERNAH DISIMPAN** ke dalam tabel `detected_item_logs` maupun ke disk penyimpanan thumbnail.
  - Hanya kelas benda bawaan yang diizinkan (`VISION_TRACKABLE_CLASSES`: `cell phone`, `remote`, `bottle`, `cup`, `laptop`, `book`, `backpack`, `handbag`, `suitcase`, `mouse`, `keyboard`, `umbrella`) yang diproses untuk fitur pencarian barang keluarga.

---

## 8. Web Dashboard "Rumah" (Tahap W)

### 8.1 Arsitektur Antarmuka & Keputusan Paket
- **React 19 + TypeScript + Vite**: Melanjutkan repositori `web/` dengan pembekuan dibuka kembali.
- **Styling**: Menggunakan **CSS Modules** dan CSS Custom Properties murni yang diturunkan dari `web/src/design-tokens.json` (tanpa Tailwind CDN).
- **Paket Tambahan**:
  1. `react-router-dom`: Untuk routing sisi klien SPA tanpa reload halaman pada 7 layar dashboard (`/`, `/perangkat`, `/asisten`, `/kamera`, `/keluarga`, `/pengaturan`, `/login`). Memastikan sesi autentikasi in-memory dan koneksi streaming WebSocket tetap bertahan antar navigasi halaman.
  2. `@tanstack/react-query`: Untuk manajemen state server (caching terstruktur, deduplikasi request HTTP, sinkronisasi background polling, serta invalidasi otomatis saat saklar/relai diubah). Mencegah boilerplate fetch manual dan memory leak.
  3. `@phosphor-icons/react`: Ikon garis outline Phosphor Regular (20px dan 24px) sesuai spesifikasi desain Quiet Domesticity (tanpa emoji).
- **Keamanan Token Autentikasi**:
  - `access_token` HANYA disimpan di memori proses JavaScript (`AuthContext` React) dan **TIDAK PERNAH disimpan di localStorage/sessionStorage** untuk mencegah pencurian token melalui serangan XSS.
  - `refresh_token` disimpan dalam **cookie httpOnly** (`Path=/api/auth`, `SameSite=Lax`, `HttpOnly=True`). Klien web tidak dapat membaca cookie lewat JS; browser otomatis menyertakan cookie ke endpoint `/api/auth/refresh` saat inisialisasi ulang sesi.
- **Penyajian Single-Origin**:
  - Backend FastAPI menyajikan berkas statis `web/dist` pada origin yang sama di port 8000. Seluruh request SPA diarahkan ke `index.html`. Hal ini mengeliminasi masalah CORS dan memungkinkan dashboard serta API berjalan dalam satu domain publik Cloudflare Tunnel.

---

## 9. Wawasan Keluarga, Estimasi Pose, & Privasi Terkelola (Tahap 6)

### 9.1 Kebijakan Privasi Ketat & Label Jujur
- **Tanpa Pengenalan Wajah**: Sistem sama sekali tidak melakukan identifikasi atau pencocokan biometrik wajah. Seluruh statistik berbasis zona ruang dan agregat rumah tangga.
- **Label UI Jujur**: Tidak membuat klaim perilaku atau atribusi individu (misal: "Aktivitas di Zona Belajar", bukan "waktu belajar anak"; "Ada HP terdeteksi di ruang tamu", bukan "anak bermain HP").
- **Fitur Ditunda ke Tahap 6B**: Lokasi HP, penghitungan "hari berturut-turut di rumah", dan saran ke luar rumah ditunda untuk menghindari over-surveillance.
- **Seluruh Fitur Default MATI**: Seluruh saklar analitik keluarga berstatus nonaktif secara default saat instalasi dan hanya dapat diaktifkan secara eksplisit oleh admin.
- **Retensi & Pembersihan Data**: Retensi data otomatis dikonfigurasi (90 hari statistik harian, 30 hari log detail). Tersedia tombol aksi "Hapus Semua Data Keluarga" dengan dialog konfirmasi yang membersihkan tabel analitik seketika.
- **Hak Akses Admin-Only (RBAC)**: Endpoint `/api/family/*` (kecuali transparansi `/transparency`) menolak pengguna `member` dan `child` dengan HTTP 403 Forbidden. Setiap akses dicatat ke dalam `audit_logs`.

### 9.2 Editor Zona Poligon & Titik Uji Spasial
- Poligon zona (koordinat normalisasi `[0..1]`) disimpan di database per kamera dengan tipe: `belajar`, `umum`, atau `berbahaya`.
- Pengujian titik terhadap poligon (*Point-in-Polygon*) menggunakan algoritma ray-casting berbasis titik kaki atau pusat bawah kotak deteksi orang: $((x_1 + x_2)/2, y_2)$.

### 9.3 Estimasi Pose & Klasifikasi Postur
- Model: **YOLO11n-pose FP32** (ONNX Runtime, 2 threads intra-op) dijalankan hanya pada frame yang mendeteksi orang (1–2 FPS).
- Postur tubuh diklasifikasikan secara geometris dari 17 titik tubuh COCO: `berdiri`, `duduk`, `berbaring`, dan `tidak diketahui`.
- Evaluasi Akurasi Jatuh: Dataset eksternal (seperti UR Fall Detection Dataset) tidak diunduh ke lingkungan lokal untuk mematuhi aturan privasi ketat ("DILARANG mengunduh rekaman luar atau membuat rekaman uji dari perangkat mana pun tanpa izin"). Status akurasi pada dataset publik dilaporkan secara jujur sebagai **TIDAK DIUKUR**. Disediakan modul skrip mandiri `scripts/eval_pose.py --video <file> --labels <file>` untuk evaluasi independen.

### 9.4 Evaluasi Post-Motion Detection (YOLO11s FP32)
- Evaluasi sapuan ambang (0.10, 0.15, 0.20, 0.25, 0.30) pada 238 gambar COCO val2017:
  * Latensi inferensi YOLO11s FP32: **289.7 ms (0.290 detik) per pass** (memenuhi syarat <= 1.5 detik).
  * Recall kelas kecil pada ambang 0.15: meningkat dari **48.14%** (YOLO11n) menjadi **54.94%** (YOLO11s), mencatatkan kenaikan terukur **+6.8% absolute gain**.
  * Diimplementasikan di `server/app/core/camera/post_motion.py` yang dipicu 1 kali ketika gerakan reda selama N detik (default 5 detik), dengan penanda `source="post_motion"`.

### 9.5 Antarmuka Notifikasi & Template Ringkasan
- Desain antarmuka `NotificationProvider` dengan implementasi default `InAppNotificationProvider` (penyimpanan DB, WebSocket live event, counter badge) dan `FCMNotificationProvider` (opsional jika berkas kredensial service account Firebase tersedia di `.env`).
- Payload FCM hanya memuat teks generik: `"Ada peringatan baru di Rumah"`. Detail kejadian sensitif tidak pernah disertakan di payload push notifikasi pihak ketiga.
- Ringkasan harian dan mingguan dihasilkan menggunakan template string lokal deterministik tanpa memanggil model bahasa LLM.
- Tool asisten percakapan `get_family_summary` dilindungi oleh saklar admin `allow_assistant_family_summary` (default MATI). Saat saklar mati, tool mengembalikan string `"dinonaktifkan"` tanpa ada data analitik yang keluar ke LLM. Saat aktif, hanya angka agregat tanpa nama dan waktu spesifik yang dibagikan.


