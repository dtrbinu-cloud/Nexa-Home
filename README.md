# Proyek "Rumah" — Smart Home + Asisten AI + Pengawasan Keluarga

Sistem Smart Home mandiri yang dirancang untuk privasi penuh (pemrosesan lokal), efisiensi hardware, dan kestabilan jangka panjang.

**Target Lingkungan Server:**
- Sistem Operasi: Windows 10
- Prosesor: Intel Core i3 Gen 4 (2 Core / 4 Thread)
- Memori: 8 GB RAM (tanpa GPU diskrit)

---

## Memulai dari Nol (Panduan Cepat)

Untuk memulai seluruh sistem dari repositori baru:

```powershell
.\scripts\setup.ps1
.\scripts\dev.ps1
```

1. **`.\scripts\setup.ps1`**: Idempoten. Memeriksa alat (Git, Python 3.11, Node.js LTS, Flutter jika `-WithMobile`), membuat virtual environment, menginstal dependensi, menyalin `.env.example` ke `.env` (tanpa menimpa), dan menjalankan verifikasi awal.
2. **`.\scripts\dev.ps1`**: Menjalankan server backend FastAPI dan server frontend secara bersamaan.

---

## Struktur Repositori (Monorepo)

```text
├── docs/               # Dokumentasi keputusan arsitektur (DECISIONS.md)
├── server/             # Backend Python 3.11 (FastAPI, SQLite WAL, SQLAlchemy, Argon2, TOTP)
│   ├── app/
│   │   ├── api/routes/ # Endpoint API (/auth, /audit-logs, /health, /test)
│   │   ├── core/       # Konfigurasi, Security (Argon2, TOTP, JWT), SetupManager, Database
│   │   ├── models/     # Model SQLAlchemy (User, RefreshToken, AuditLog)
│   │   └── main.py     # Entrypoint aplikasi FastAPI
│   ├── data/           # Database SQLite lokal (rumah.db)
│   └── tests/          # Pengujian otomatis backend (pytest)
├── app/                # Aplikasi Mobile Utama (Android Native Flutter)
│   ├── lib/
│   │   ├── components/ # Komponen dasar (AppButton, AppCard, AppSwitch, AppBadge, AppInput, AppToast, EmptyState)
│   │   ├── core/       # State Riverpod, ApiClient Dio, StorageService
│   │   ├── screens/    # SetupWizard, Login, Verify2FA, Shell (6 Tab), DesignScreen (Debug)
│   │   └── theme/      # tokens.dart (dihasilkan otomatis dari design-tokens.json)
│   └── assets/fonts/   # Font lokal offline (Public Sans & IBM Plex Mono)
├── web/                # Frontend Web Cadangan (React 19 + Vite - STATUS: DIBEKUKAN)
├── firmware/           # Firmware MicroPython untuk ESP32
│   └── legacy/         # Cadangan firmware lama (.gitignore aktif)
├── camera-app/         # Direktori persiapan modul kamera HP bekas (Tahap 4)
├── scripts/
│   ├── setup.ps1       # Satu perintah setup otomatis lingkungan Windows
│   ├── dev.ps1         # Runner multi-proses layanan pengembangan
│   ├── gen_flutter_theme.py # Generator tokens.dart dari design-tokens.json
│   └── check_tokens.py # Linter otomatis kepatuhan token desain (Web & Flutter)
├── .env.example        # Template konfigurasi rahasia & parameter sistem
├── .gitignore          # Pengabaian rahasia, venv, node_modules, build artifacts
└── pyproject.toml      # Konfigurasi pytest dan ruff
```

---

## Alur Autentikasi & Setup Wizard (Tahap 1)

1. **Setup Admin Sekali Pakai (One-Time Console Code):**
   - Saat backend pertama kali dijalankan tanpa akun admin di database, server secara otomatis mencetak kode acak sekali pakai di konsol terminal (misal: `RUMAH-A8F2K9`).
   - Endpoint `POST /api/auth/setup-admin` hanya dapat diakses melalui **Localhost atau Jaringan Lokal (LAN privat)**. Akses dari IP publik otomatis ditolak (HTTP 403).
   - Admin pertama wajib memasangkan **TOTP 2FA** dan menerima **8 kode pemulihan (recovery codes)** sekali pakai.
2. **Autentikasi & Peran (RBAC):**
   - Kata sandi di-hash menggunakan **Argon2id**.
   - Login admin mengembalikan status `2fa_required` dan membutuhkan kode TOTP 6 digit atau recovery code.
   - Peran pengguna didukung secara ketat di backend: `admin`, `member`, `child`.
   - Log audit dicatat otomatis pada setiap aktivitas autentikasi dan pembuatan akun di tabel `audit_logs`.

---

## Pengujian dan Pemeriksaan Mutu

### 1. Pengujian Backend (pytest)
```powershell
.\server\.venv\Scripts\python.exe -m pytest -v
```

### 2. Pemeriksaan Kepatuhan Token Desain (Web & Flutter)
```powershell
.\server\.venv\Scripts\python.exe scripts\check_tokens.py
```
*Memverifikasi tidak ada warna HEX `#...`, `Color(0x...)`, atau `Colors.xxx` yang di-hardcode di luar berkas token.*

### 3. Pengujian Aplikasi Flutter
```powershell
cd app
flutter test
flutter analyze
cd ..
```

### 4. Build APK Release Android (Split ABI)
```powershell
cd app
flutter build apk --release --split-per-abi
cd ..
```
*Hasil APK arsitektur modern tersimpan di `app/build/app/outputs/flutter-apk/app-arm64-v8a-release.apk` (~16.9 MB).*

### 5. Cara Menguji Aplikasi Android di HP Asli lewat LAN
Aplikasi telah dilengkapi konfigurasi [network_security_config.xml](file:///c:/Users/DELL/Downloads/Nexa%20Home/app/android/app/src/main/res/xml/network_security_config.xml) untuk mengizinkan lalu lintas HTTP lokal di jaringan pribadi (RFC 1918):
1. Pastikan laptop/server dan HP terhubung ke WiFi/LAN yang sama.
2. Cari IP lokal server (contoh: jalankan `ipconfig`, misal `192.168.1.50`).
3. Pasang APK (`app-arm64-v8a-release.apk`) di HP Android.
4. Buka aplikasi, masuk ke menu **Pengaturan**, dan ubah Alamat Server menjadi `http://192.168.1.50:8000`.
5. Aplikasi akan langsung terhubung ke server backend secara lancar tanpa hambatan blokir cleartext Android.

---

## Catatan Keamanan Hardware (ESP32 & Sensor MQ-2)

> [!WARNING]
> **PENTING — Pembagi Tegangan ADC ESP32:**
> Output analog dari sensor gas MQ-2 menghasilkan sinyal hingga **5,0 V**, sedangkan batas toleransi ADC ESP32 (pin GPIO 33) maksimal adalah **3,3 V**. 
> Anda **WAJIB** memasang rangkaian pembagi tegangan (*voltage divider*) menggunakan 2 resistor (misalnya R1 = 10kΩ ke pin A0 sensor, R2 = 20kΩ ke GND, dan titik tengah dihubungkan ke GPIO 33 ESP32) agar chip ESP32 tidak terbakar atau rusak permanen.

---

## Status Tahap Pengembangan

- [x] **Tahap 0: Fondasi Repo dan Keputusan** (Selesai)
- [x] **Tahap 1: Backend Inti, Autentikasi, dan App Android Flutter** (Selesai)
- [x] **Tahap 2: Kontrol IoT (MQTT) dan Firmware Baru** (Selesai)
- [ ] **Tahap 3: Asisten Percakapan dan Suara (DeepSeek + TTS/STT)**
- [ ] **Tahap 4: Kamera dari HP Bekas (WebRTC / MediaMTX)**
- [ ] **Tahap 5: Vision AI dan Pencarian Barang (YOLO11 ONNX)**
- [ ] **Tahap 6: Insight Keluarga (Aturan Otomasi & Privasi)**
- [ ] **Tahap 7: Pengerasan Keamanan dan Peluncuran**
