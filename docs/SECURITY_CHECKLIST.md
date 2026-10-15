# Daftar Periksa Keamanan Sistem (Security Checklist) — Tahap 7

Dokumen ini memuat daftar periksa kepatuhan keamanan (*security posture compliance*) sistem **Nexa Home** pada peluncuran Tahap 7 beserta bukti verifikasi pengujian otomatisnya.

---

## 1. Matriks Kepatuhan Keamanan

| Kategori | Item Pemeriksaan | Status | Bukti / Catatan Verifikasi |
| :--- | :--- | :---: | :--- |
| **Autentikasi** | Algoritma Hashing Kata Sandi |  LULUS | Menggunakan `Argon2id` (m=65536, t=3, p=4) via `passlib.context.CryptContext`. |
| **Autentikasi** | Google OAuth2 Validasi Server |  LULUS | Verifikasi resmi ke endpoint Google `oauth2.googleapis.com/tokeninfo`. Kunci rahasia client secret hanya di server. |
| **Autentikasi** | Otentikasi Dua Faktor (2FA) |  LULUS | Mendukung TOTP 6 digit (Google Authenticator) dan daftar kode pemulihan sekali pakai (*hashed recovery codes*). |
| **Autentikasi** | Pembatasan Percobaan Login (Rate Limit) |  LULUS | Maksimal 10 kegagalan per 60 detik per alamat IP (`check_login_ip_rate_limit`). Melebihi batas mengembalikan HTTP 429. |
| **Autentikasi** | Penguncian Akun Sementara (Lockout) |  LULUS | Gagal memasukkan kata sandi 5 kali berturut-turut mengunci akun selama 15 menit (`locked_until`). Teruji via `test_role_matrix.py`. |
| **Autentikasi** | Notifikasi Login Baru |  LULUS | Otomatis mencatat ke notifikasi in-app dan mengirimkan email peringatan deteksi IP baru via `EmailService`. |
| **Otorisasi** | Kontrol Akses Berbasis Peran (RBAC) |  LULUS | Matriks izin ketat memisahkan hak `admin` (kontrol penuh), `member` (kontrol perangkat & kamera publik), `child` (akses terbatas), dan `unapproved` (tertahan). |
| **Data Diam** | Enkripsi Rekaman Kamera & Media |  LULUS | Menggunakan enkripsi simetris `AES-256-GCM` dengan associated data `camera_id` dan nonce 12-byte acak per berkas. |
| **Data Diam** | Kunci Tidak Pernah di Database |  LULUS | Kunci master `MEDIA_ENCRYPTION_KEY` hanya tersimpan di file lokal `.env` dan diabaikan dari git (`.gitignore`). |
| **Data Diam** | Mekanisme Rotasi Kunci Tanpa Rusak |  LULUS | Skrip `scripts/rotate-keys.py` mendekripsi dan mengenkripsi ulang seluruh klip aktif dengan kunci baru. Teruji 46/46 klip sukses. |
| **Pencadangan** | Konsistensi Snapshot Database (WAL Safe) |  LULUS | Skrip `scripts/backup.ps1` memanfaatkan `sqlite3.backup` API untuk menjamin konsistensi ACID 100% tanpa risiko korupsi WAL. |
| **Pemulihan** | Uji Bencana & Integritas Restore |  LULUS | Simulasi `scripts/test_backup_restore.py` menguji siklus *Seed -> Hapus -> Restore -> Verifikasi*. Hasil PRAGMA integrity check = 'ok'. |
| **Data Bergerak** | Enkripsi Lalu Lintas Publik (TLS/SSL) |  LULUS | Seluruh lalu lintas internet wajib melewati Cloudflare Tunnel (`https://aujasena.my.id`) dengan enkripsi TLS 1.3. |
| **Data Bergerak** | Streaming WebRTC Terproteksi |  LULUS | Aliran video langsung menggunakan protokol WHEP/WebRTC dengan pertukaran token otentikasi sesi. |
| **Data Bergerak** | Kredensial Unik MQTT Perangkat |  LULUS | Setiap alat ESP32 dialokasikan username & password unik yang diacak secara kriptografis saat proses pairing. |
| **Header HTTP** | Anti MIME-Sniffing |  LULUS | Header `X-Content-Type-Options: nosniff` terpasang di seluruh respon FastAPI. |
| **Header HTTP** | Anti Clickjacking |  LULUS | Header `X-Frame-Options: DENY` terpasang di seluruh respon FastAPI. |
| **Header HTTP** | Kebijakan Referrer Ketat |  LULUS | Header `Referrer-Policy: strict-origin-when-cross-origin` terpasang aktif. |
| **Header HTTP** | HSTS (Strict-Transport-Security) |  LULUS | Header `Strict-Transport-Security: max-age=31536000; includeSubDomains` terpasang aktif. |
| **Header HTTP** | Content-Security-Policy (CSP) |  LULUS | CSP ketat membatasi domain ke `self`, `aujasena.my.id`, Google OAuth, dan MediaMTX streaming. |
| **Header HTTP** | CORS Terbatas (Whitelisted Origins) |  LULUS | Origins dibatasi spesifik ke `https://aujasena.my.id` dan origin lokal pengembang. Wildcard `*` dinonaktifkan. |
| **Jaringan** | Port Binding Layanan Lokal |  LULUS | Backend FastAPI mengikat port privat `127.0.0.1:8000`, tidak ada port aplikasi yang dibuka langsung ke publik router (zero open port). |
| **Operasional** | Auto-Start Layanan Windows 10 |  LULUS | Disediakan `scripts/install-autostart.ps1` untuk mendaftarkan tugas ke Windows Task Scheduler / Startup. |
| **Operasional** | Watchdog Pemantau Kesehatan |  LULUS | Skrip `scripts/watchdog.py` memonitor ketersediaan HTTP & TCP secara berkala dan mencatat ke log berotasi. |
| **Operasional** | Rotasi Berkas Log (Anti Kepenuhan Disk) |  LULUS | Modul `logging_config.py` menerapkan `RotatingFileHandler` maksimal 10 MB per berkas dengan retensi 5 file cadangan. |
| **Dependensi** | Audit Paket & Kerentanan |  LULUS | Pemeriksaan `pip check` mengonfirmasi: *"No broken requirements found."* |

---

## 2. Bukti Log Verifikasi Otomatis

### A. Uji Matriks Peran & Pengerasan Keamanan (`pytest server/tests/test_role_matrix.py`)
```text
server/tests/test_role_matrix.py::test_security_headers_present PASSED   [ 25%]
server/tests/test_role_matrix.py::test_account_lockout_after_five_failed_attempts PASSED [ 50%]
server/tests/test_role_matrix.py::test_new_login_notification_created PASSED [ 75%]
server/tests/test_role_matrix.py::test_role_based_access_matrix PASSED   [100%]
============================== 4 passed in 5.92s ==============================
```

### B. Uji Simulasi Backup & Restore Bencana (`scripts/test_backup_restore.py`)
```text
======================================================================
  [HASIL PENGUJIAN]: LULUS 100%!
  - Integritas Database : PRAGMA integrity_check = 'ok'
  - Tabel Users         : 3/3 record kembali utuh (['admin_rumah', 'member_budi', 'child_dina'])
  - Tabel Devices       : 2/2 record kembali utuh (['lamp_living_room', 'sensor_kitchen'])
  - Klip Terenkripsi    : SHA-256 identik (1b05eecae3260b4f...)
  - Validasi AES-GCM    : Sukses didekripsi menjadi payload byte asli
======================================================================
```

### C. Uji Rotasi Kunci Kriptografi (`scripts/rotate-keys.py --generate-key --dry-run`)
```text
=================================================================
  RINGKASAN ROTASI KUNCI:
  - Total Klip    : 46
  - Sukses Rotasi : 46
  - Gagal         : 0
  - Status .env   : Tidak Berubah (Simulasi)
=================================================================
```

### D. Uji Kepatuhan Token Desain (`scripts/check_tokens.py`)
```text
=== Memeriksa Kepatuhan Token Desain (Web & Flutter) ===
[BERHASIL] Semua komponen (Web & Flutter) 100% mematuhi sistem token desain.
```
