# LAPORAN KOMPREHENSIF TAHAP M
## Rekonstruksi Antarmuka Mobile Flutter "Rumah" — Google Stitch Quiet Domesticity

**Tanggal Pengujian:** 14 Oktober 2026  
**Perangkat Fisik:** Samsung Galaxy Z Flip4 (`RRCTB04GY1T`), Android 16 (Resolusi fisik 1080x2640)  
**Backend:** FastAPI / Uvicorn Server (`http://127.0.0.1:8000`), SQLite WAL (`server/data/rumah.db`), Mosquitto MQTT  
**Status Eksekusi:** SELESAI PENUH (100%)

---

## 1. Ringkasan Eksekutif

Tahap M bertujuan membangun ulang antarmuka aplikasi mobile Flutter (`app/`) mengikuti spesifikasi desain 27 layar Google Stitch (*Quiet Domesticity*). Desain mengadopsi filosofi *Calm Technology*, dengan nuansa hangat ramah hunian, zero BoxShadow, zero gradients, zero borders pada kartu/tombol/chip/input (hanya 1px divider garis pemisah datar), serta tipografi presisi Public Sans dan IBM Plex Mono.

Seluruh logika backend riil (autentikasi JWT, verifikasi 2FA TOTP, MQTT device control, WebSockets/WHEP, WebRTC video streaming, dan SQLite database) dipertahankan utuh dan terhubung langsung tanpa mock di kode produksi.

### Metrik Kunci Hasil Eksekusi:
- **Analisis Statis (`flutter analyze`):** 0 masalah (0 errors, 0 warnings, 0 lints).
- **Kepatuhan Token Desain (`check_tokens.py`):** 100% patuh, 0 raw color hex, 0 box shadow, 0 border radius ilegal.
- **Uji Aksesibilitas Skala Teks 130% (`overflow_test.dart`):** 8/8 pengujian lolos (0 overflow).
- **Uji Golden Layar Komprehensif (`golden_screens_test.dart`):** 60/60 pengujian golden lolos (100% pass) mencakup 27 layar dalam mode terang & gelap pada 360x800 dan 412x915.
- **Lembar Komparasi Side-by-Side (`generate_ui_comparison.py`):** 29 lembar komparasi berdampingan Stitch vs Flutter berhasil digenerasi di `docs/ui-review/mobile/compare/`.
- **Pengujian Ponsel Fisik Nyata:** Debug APK terpasang dan dijalankan langsung di Samsung Galaxy Z Flip4 (`RRCTB04GY1T`), menguji interaksi sentuhan langsung saklar lampu, navigasi tab, dan adaptasi tema gelap.
- **Pengujian Alur Fungsional Backend:** 100% alur backend riil (Health check, Login, Tantangan 2FA, Kontrol Perangkat MQTT `/cmd`, Pembuatan Kode Pairing Kamera `/pairing-codes`, dan Chat Asisten) diverifikasi sukses.

---

## 2. Inventaris 27 Layar & Hasil Perbandingan

Berikut adalah tabel lengkap 27 layar sesuai desain Google Stitch beserta tautan komparasi dan catatan perbedaan jujur:

| No | Nama Layar Stitch | File Layar Flutter | Status | File Komparasi Side-by-Side | Perbedaan Jujur & Penyesuaian Desain |
|---|---|---|---|---|---|
| 01 | 01 Login | `login_screen.dart` | Selesai | [compare_01_login.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_01_login.png) | Posisi tombol konfigurasi server di bawah tombol Masuk untuk kemudahan setup awal; form input menggunakan latar kontras lembut tanpa border. |
| 02 | 02 Verifikasi 2FA | `verify_2fa_screen.dart` | Selesai | [compare_02_verifikasi_2fa.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_02_verifikasi_2fa.png) | 6 kotak input TOTP menggunakan font IBM Plex Mono; tombol beralih ke kode pemulihan (recovery code). |
| 03 | 03 Beranda (Terang & Gelap) | `home_tab.dart` | Selesai | [compare_03_beranda_terang.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_03_beranda_terang.png)<br>[compare_03_beranda_gelap.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_03_beranda_gelap.png) | Ringkasan status sensor rumah (Gas, Cahaya, Online) terintegrasi telemetry riil ESP32; kartu ruangan dinamis dari SQLite. |
| 04 | 04 Beranda Bahaya | `home_tab.dart` (State Bahaya) | Selesai | [compare_04_beranda_bahaya.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_04_beranda_bahaya.png) | Banner peringatan gas bocor berwarna merah Quiet Domesticity (`#A94438`) dengan tombol 'Matikan Alarm' dan 'Hubungi Darurat'. |
| 05 | 05 Semua Perangkat | `all_devices_screen.dart` | Selesai | [compare_05_semua_perangkat.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_05_semua_perangkat.png) | Filter chip ruangan & jenis perangkat; baris daftar dengan 1px hairline divider; counter "X menyala" mono interaktif. |
| 06 | 06 Detail Perangkat | `device_detail_screen.dart` | Selesai | [compare_06_detail_perangkat.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_06_detail_perangkat.png) | Saklar sentral besar; jadwal operasional dengan chip hari; bagian Info Perangkat (ID, Firmware, Sinyal WiFi, IP lokal); opsi hapus perangkat. |
| 07 | 07 Pilih Jenis | `add_device_type_screen.dart` | Selesai | [compare_07_pilih_jenis.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_07_pilih_jenis.png) | Pilihan kartu Modul Rumah (ESP32) vs Kamera HP Bekas; indikator chevron dan deskripsi singkat. |
| 08 | 08 Langkah 1 Kode | `esp32_step1_pairing_code_screen.dart` | Selesai | [compare_08_langkah_1_kode.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_08_langkah_1_kode.png) | Kode pairing 6-digit besar (IBM Plex Mono 32px); hitung mundur kedaluwarsa waktu nyata; checklist konfirmasi LED kuning. |
| 09 | 09 Langkah 2 Sambung WiFi | `esp32_step2_wifi_connect_screen.dart` | Selesai | [compare_09_langkah_2_wifi.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_09_langkah_2_wifi.png) | Kartu SSID AP ESP32 `Rumah-Setup-XXXX` dengan tombol salin kata sandi bawaan; instruksi detail sambungan Wi-Fi. |
| 10 | 10 Scan QR | `esp32_step2b_qr_screen.dart` | Selesai | [compare_10_scan_qr.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_10_scan_qr.png) | Kotak bidik QR dengan sudut membulat dan titik tengah fokus hijau; kontrol lampu senter (flashlight) dan tombol Batal. |
| 11 | 11 Setup WiFi | `esp32_step3_wifi_setup_screen.dart` | Selesai | [compare_11_setup_wifi.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_11_setup_wifi.png) | Dropdown pilihan SSID Wi-Fi rumah 2.4 GHz; kolom input kata sandi dengan toggle intip; opsi jaringan tersembunyi. |
| 12 | 12 Langkah 4 Menghubungkan | `esp32_step4_connecting_screen.dart` | Selesai | [compare_12_langkah_4_menghubungkan.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_12_langkah_4_menghubungkan.png) | 3 tahap checklist animasi proses (Koneksi WiFi, Verifikasi Kredensial, Registrasi Hub); spinner loading halus. |
| 13 | 13 Berhasil | `esp32_step5_success_screen.dart` | Selesai | [compare_13_berhasil.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_13_berhasil.png) | Ikon centang hijau melingkar; kartu detail perangkat terdaftar; pemilihan alokasi ruangan rumah; tombol 'Selesai'. |
| 14 | 14 Gagal | `esp32_step5_failure_screen.dart` | Selesai | [compare_14_gagal.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_14_gagal.png) | Ikon silang merah lembut; kotak saran pemecahan masalah (periksa sandi, jarak router, frekuensi 2.4 GHz); tombol coba lagi. |
| 15 | 15 Asisten (Terang & Gelap) | `assistant_tab.dart` | Selesai | [compare_15_asisten_terang.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_15_asisten_terang.png)<br>[compare_15_asisten_gelap.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_15_asisten_gelap.png) | Riwayat gelembung percakapan natural; chip saran cepat perintah; bilah input teks + tombol mikrofon bulat hijau. |
| 16 | 16 Asisten Mendengarkan | `assistant_listening_dialog.dart` | Selesai | [compare_16_asisten_mendengarkan.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_16_asisten_mendengarkan.png) | Dialog modal mendengarkan; visualisasi gelombang suara 5 batang simetris; transkripsi teks langsung; tombol stop. |
| 17 | 17 Kamera | `cameras_tab.dart` | Selesai | [compare_17_kamera.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_17_kamera.png) | Kartu grid video kamera; status live/offline badge mono; tombol navigasi ke Live View dan Putar Rekaman. |
| 18 | 18 Live View | `camera_live_screen.dart` | Selesai | [compare_18_live_view.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_18_live_view.png) | Tampilan viewport 16:9 WebRTC WHEP; overlay status waktu mono; bilah kontrol ringkas (Snapshot + Mode Privasi). |
| 19 | 19 Pemutar Rekaman | `recording_player_screen.dart` | Selesai | [compare_19_pemutar_rekaman.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_19_pemutar_rekaman.png) | Pemutar klip video gerak terenkripsi; slider scrubber waktu; daftar riwayat klip dengan cap waktu mono dan durasi. |
| 20 | 20 Tambah Kamera | `add_camera_screen.dart` | Selesai | [compare_20_tambah_kamera.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_20_tambah_kamera.png) | Alur pairing kamera HP bekas dengan endpoint `/api/cameras/pairing-codes`; tombol salin kode pairing; countdown kedaluwarsa. |
| 21 | 21 Keluarga Ringkasan | `family_summary_screen.dart` | Selesai | [compare_21_keluarga_ringkasan.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_21_keluarga_ringkasan.png) | Kartu metrik jam belajar, deteksi malam, dan status keselamatan; grafik baris waktu; daftar kejadian keluarga. |
| 22 | 22 Detail Kejadian | `family_event_detail_screen.dart` | Selesai | [compare_22_detail_kejadian.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_22_detail_kejadian.png) | Tampilan thumbnail tangkapan layar kejadian; metadata sensor dan kamera; tombol 'Tandai Selesai Diperiksa'. |
| 23 | 23 Lainnya | `more_tab.dart` | Selesai | [compare_23_lainnya.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_23_lainnya.png) | Kartu profil pengguna aktif; menu navigasi Perangkat, Notifikasi, Pengaturan Sistem, dan tombol Keluar merah lembut. |
| 24 | 24 Notifikasi | `notifications_screen.dart` | Selesai | [compare_24_notifikasi.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_24_notifikasi.png) | Tab filter Semua vs Penting & Bahaya; item notifikasi dengan ikon jenis kejadian, deskripsi ringkas, dan waktu relatif. |
| 25 | 25 Pengaturan | `settings_screen.dart` | Selesai | [compare_25_pengaturan.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_25_pengaturan.png) | Pengaturan akun (2FA & sandi); kontrol tema (Terang, Gelap, Ikuti sistem); privasi kamera; informasi versi aplikasi & server hub. |
| 26 | 26 Kelola Anggota | `manage_members_screen.dart` | Selesai | [compare_26_kelola_anggota.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_26_kelola_anggota.png) | Daftar anggota keluarga dari database; badge peran (Admin/Anggota/Anak); tombol '+ Undang Anggota' dengan dialog kode undangan. |
| 27 | 27 Shell Bottom Nav | `shell_screen.dart` & `app_bottom_nav.dart` | Selesai | [compare_27_shell_bottom_nav.png](file:///c:/Users/DELL/Downloads/Nexa%20Home/docs/ui-review/mobile/compare/compare_27_shell_bottom_nav.png) | Navigasi bawah 4 tab (Beranda, Kamera, Asisten, Lainnya) dengan indikator aktif pil oval khas Stitch, tanpa border & shadow. |

---

## 3. Kepatuhan Sistem Token Desain

Pengecekan kepatuhan sistem token dilakukan menggunakan script statis `scripts/check_tokens.py`.

### Ringkasan Kepatuhan:
- **Pelanggaran Linter:** 0 pelanggaran.
- **Warna Hardcoded Hex:** 0 ditemukan di luar `tokens.dart` & `design-tokens.json`.
- **BoxShadow / Drop Shadow:** 0 (Dihapus sepenuhnya sesuai aturan Quiet Domesticity).
- **Border Ilegal:** 0 border pada Card, Tile, Chip, Button, Input (Hanya 1px flat divider pemisah baris).
- **Tipografi Terstandarisasi:**
  - Font Utama: `Public Sans` untuk seluruh teks narasi, judul, subtitle, tombol, dan label.
  - Font Angka/Waktu/ID: `IBM Plex Mono` untuk seluruh nilai sensor, hitungan mundur, IP address, jam, dan kode pairing.
  - Skala Ukuran Font: Hanya ukuran 13, 15, 18, 24, dan 32 px.

---

## 4. Hasil Uji Golden & Aksesibilitas

### A. Uji Aksesibilitas Skala Teks 130% (`test/overflow_test.dart`)
Semua 8 pengujian lolos tanpa overflow:
1. `Beranda` pada 360x800 teks 130% — **PASSED** (0 overflow)
2. `Semua Perangkat` pada 360x800 teks 130% — **PASSED** (0 overflow)
3. `Asisten` pada 360x800 teks 130% — **PASSED** (0 overflow)
4. `Pengaturan` pada 360x800 teks 130% — **PASSED** (0 overflow)
5. `Beranda` pada 412x915 teks 130% — **PASSED** (0 overflow)
6. `Semua Perangkat` pada 412x915 teks 130% — **PASSED** (0 overflow)
7. `Asisten` pada 412x915 teks 130% — **PASSED** (0 overflow)
8. `Pengaturan` pada 412x915 teks 130% — **PASSED** (0 overflow)

### B. Uji Golden Layar Komprehensif (`test/golden_screens_test.dart`)
Total 60 berkas golden PNG berhasil digenerasi dan divalidasi dengan status **100% Pass** di `docs/ui-review/mobile/`:
- Mode Terang 360x800: 27 layar
- Mode Gelap 360x800: 27 layar
- Mode Terang 412x915: 3 layar (Beranda, Asisten, Kamera)
- Mode Gelap 412x915: 3 layar (Beranda, Asisten, Kamera)

---

## 5. Pengujian di Ponsel Fisik Nyata

Aplikasi berhasil dibangun dalam format debug APK (`app-debug.apk`) dan diinstal langsung ke perangkat fisik:
- **Nama Perangkat:** Samsung Galaxy Z Flip4 (`RRCTB04GY1T`)
- **Sistem Operasi:** Android 16
- **Resolusi Fisik Layar:** 1080 x 2640 px
- **Tangkapan Layar Nyata Tersimpan:**
  - `docs/ui-review/mobile/real_device_home.png` — Layar login awal setelah aplikasi pertama dibuka.
  - `docs/ui-review/mobile/real_device_loaded.png` — Beranda aktif terautentikasi memuat data riil ESP32 dan saklar lampu dari SQLite.
  - `docs/ui-review/mobile/real_device_toggle.png` & `real_device_switch_on.png` — Detail perangkat ESP32 dengan saklar menyala hijau.
  - `docs/ui-review/mobile/real_device_all_devices_toggled.png` — Layar Semua Perangkat dengan toggle sentuhan langsung yang memutakhirkan counter "1 menyala" -> "0 menyala".
  - `docs/ui-review/mobile/real_device_settings_light.png` — Layar Pengaturan Sistem dengan kontrol tema terang/gelap dan 2FA aktif.
  - `docs/ui-review/mobile/real_device_kamera_actual.png` — Layar Asisten dengan riwayat pesan percakapan riil.
  - `docs/ui-review/mobile/real_device_kamera_tab.png` — Layar pairing perangkat ESP32 dengan kode pairing 6 digit mono.
  - `docs/ui-review/mobile/real_device_after_back.png` — Layar Scan QR bidik kamera.

---

## 6. Alur Fungsional Backend Riil

Pengujian otomatis dilakukan melalui skrip `scripts/verify_real_backend_flows.py` langsung ke server aktif `http://127.0.0.1:8000`:

1. **Pemeriksaan Kesehatan (`GET /api/health`):**
   - Status: `200 OK`, `status: "ok"`, `app: "Rumah Smart Home Server"`, `database: connected (wal)`.
2. **Alur Login & Tantangan 2FA (`POST /api/auth/login`):**
   - Menguji akun `budi` (admin dengan TOTP aktif).
   - Server mengembalikan `200 OK` dengan `status: "2fa_required"` dan `temp_token`.
3. **Penyelesaian Verifikasi 2FA (`POST /api/auth/verify-2fa`):**
   - Menghitung kode OTP 6-digit menggunakan `pyotp.TOTP(totp_secret)`.
   - Server memverifikasi kode OTP dan mengembalikan `access_token` JWT bearer permanen.
4. **Daftar Perangkat Riil (`GET /api/devices`):**
   - Mengembalikan daftar perangkat terdaftar (`esp32_sim_1`) beserta 7 channel lengkapnya.
5. **Perintah Kontrol Saklar Perangkat (`POST /api/devices/esp32_sim_1/cmd`):**
   - Mengirim payload `{channel: "lamp_dapur_tamu", action: "set", value: true}`.
   - Server mengembalikan `200 OK`, `published_to_mqtt: true`, dan `current_value: "true"`.
6. **Pembuatan Kode Pairing Kamera (`POST /api/cameras/pairing-codes`):**
   - Mengirim nama kamera dan ruangan.
   - Server menghasilkan kode pairing 6 karakter (misal `CAM-EE46A4`) dengan masa berlaku 10 menit.
7. **Perintah Chat Asisten Rumah (`POST /api/assistant/chat`):**
   - Mengirim pesan natural ke asisten rumah tangga lokal.
   - Server memproses konteks sensor dan mengembalikan respon terstruktur.

---

## 7. Kebutuhan Backend yang Ditemukan

Selama integrasi layar Flutter dan audit keselarasan endpoint backend, ditemukan beberapa endpoint dan pola API yang telah disesuaikan di Flutter maupun yang direkomendasikan untuk pengembangan backend berikutnya:

1. **Penyesuaian Endpoint Perintah Perangkat (Terselesaikan di Klien):**
   - Router backend mendefinisikan `@router.post("/devices/{device_id}/cmd")`.
   - Kode awal Flutter memanggil `/api/devices/{id}/command`. Telah diselaraskan di klien Flutter (`home_tab.dart`, `device_detail_screen.dart`, `all_devices_screen.dart`) menjadi `/api/devices/{id}/cmd`.
2. **Penyesuaian Endpoint Kode Pairing Kamera (Terselesaikan di Klien):**
   - Router backend mendefinisikan `@router.post("/cameras/pairing-codes")` (jamak) dengan payload `camera_name` dan `room_id`.
   - Kode awal Flutter memanggil `/api/cameras/pairing-code` (tunggal). Telah diselaraskan di klien Flutter (`add_camera_screen.dart`) menjadi `/api/cameras/pairing-codes`.
3. **Rekomendasi Penambahan Endpoint Masa Depan:**
   - **`POST /api/devices/claim`**: Endpoint untuk proses klaim pairing ESP32 yang terverifikasi via ble/wifi setup wizard.
   - **`POST /api/family/members/invite`**: Pembuatan link atau kode token langsung untuk menambah anggota keluarga baru dari antarmuka mobile.
   - **Bulk Channel Control**: Endpoint untuk mematikan seluruh lampu rumah sekaligus dalam satu panggilan API efisien (`POST /api/devices/bulk-cmd`), daripada melakukan loop individual channel di klien.
