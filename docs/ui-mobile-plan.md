# Rencana Implementasi Tampilan Mobile App Flutter (app/) — Google Stitch

Dokumen ini memetakan 27 layar desain Google Stitch (*Quiet Domesticity*) ke arsitektur berkas Flutter di `app/`, daftar endpoint API yang digunakan, serta tabel pemetaan ikon Material Symbols ke Phosphor Icons.

---

## 1. Pemetaan 27 Layar Stitch ke Berkas Flutter

| No | Layar Stitch | Status Berkas | Berkas Flutter (`app/lib/`) | Endpoint Backend | Keterangan / Cacat Stitch yang Dibenahi |
|---|---|---|---|---|---|
| 1 | `1._login_rumah` | Ganti | `screens/login_screen.dart` | `POST /auth/login`, `GET /auth/me` | Margin 24px, input inset focus border aksen 2px, tombol 48px, tanpa border/shadow. |
| 2 | `2._kode_verifikasi_rumah` | Ganti | `screens/verify_2fa_screen.dart` | `POST /auth/2fa/verify` | 6 kotak digit mono, tombol 48px, tautan kode cadangan. |
| 3 | `3._beranda_rumah` (Terang/Gelap) | Ganti | `screens/tabs/home_tab.dart` | `GET /devices`, `POST /devices/{id}/command`, `GET /family/events`, `GET /audit/logs` | Status dot ok 8px, Gas angka mono tanpa satuan, Cahaya Terang/Gelap, Tile radius 24, Bottom Nav 4 tab. |
| 4 | `4._beranda_bahaya_rumah` | Ganti (Varian) | `screens/tabs/home_tab.dart` | Sama seperti Beranda + `POST /devices/{id}/command` (sirine) | Komponen Beranda yang SAMA + Banner bahaya solid di bagian atas ("Gas terdeteksi di Dapur", mono "1820 dari batas 1500", tombol Bunyikan/Matikan). |
| 5 | `5._semua_perangkat_rumah` | Baru | `screens/all_devices_screen.dart` | `GET /devices`, `POST /devices/{id}/command` | Sub-layar (TANPA bottom nav), filter chip horizontal, kelompok per ruangan, sensor gas tanpa ppm, offline tanpa toggle. |
| 6 | `6._detail_perangkat_lampu_rumah` | Baru | `screens/device_detail_screen.dart` | `GET /devices/{id}`, `POST /devices/{id}/command`, `DELETE /devices/{id}`, `GET /automations` | Perbaiki artefak font Stitch (ganti teks "lightbulb" jadi ikon Phosphor), toggle 56x32, jadwal, info device mono, konfirmasi hapus. |
| 7 | `7._tambah_perangkat_pilih_jenis_rumah` | Ganti | `screens/add_device/choose_type_screen.dart` | - | 2 opsi: "Modul Rumah (ESP32)" dan "Kamera dari HP bekas". Tepi ke tepi, tanpa bingkai abu-abu mockup. |
| 8 | `8._langkah_1_kode_pairing_rumah` | Ganti | `screens/add_device/esp32_step1_code_screen.dart` | Belum ada di server (status jujur) | Indikator langkah 1/4, kode pairing mono 6 digit, timer mono, info LED kuning. |
| 9 | `9._langkah_2_sambung_wifi_alat_rumah` | Ganti | `screens/add_device/esp32_step2_connect_wifi_screen.dart` | - | Pilihan "Scan QR" dan "Isi manual" (SSID + sandi unik + tombol salin). |
| 10 | `10._scan_qr_rumah` | Ganti | `screens/add_device/esp32_qr_scan_screen.dart` | - | Font Public Sans (bukan serif Times), hilangkan chip fiktif "SENSOR: AKTIF", kotak bidik kamera. |
| 11 | `11._langkah_3_setup_wifi_rumah_rumah` | Ganti | `screens/add_device/esp32_step3_wifi_setup_screen.dart` | - | Tombol "Hubungkan" STICKY di bawah layar (tidak terpotong), buang catatan "Konektivitas" dan "Terverifikasi lokal". |
| 12 | `12._langkah_4_menghubungkan_rumah` | Ganti | `screens/add_device/esp32_step4_connecting_screen.dart` | - | Stepper vertikal progres koneksi WiFi & server, estimasi 30 detik. |
| 13 | `13._berhasil_tambah_perangkat_rumah` | Ganti | `screens/add_device/esp32_success_screen.dart` | - | Kartu sukses / bottom sheet hasil pairing, form nama & ruangan perangkat, tombol selesai. |
| 14 | `14._gagal_tambah_perangkat_rumah` | Ganti | `screens/add_device/esp32_error_screen.dart` | - | SATU layar dengan 3 varian state: Sandi WiFi salah, Kode pairing kedaluwarsa, Server tidak terjangkau. Font Public Sans. |
| 15 | `15._asisten_rumah` (Terang/Gelap) | Ganti | `screens/tabs/assistant_tab.dart` | `POST /assistant/command`, WebSocket assistant stream | Bubble chat, chip saran dengan margin 12px dan padding horizontal 16px (tidak terpotong), tanpa ikon sparkle/AI bintang. |
| 16 | `16._asisten_mendengarkan_rumah` | Ganti | `components/assistant_listening_sheet.dart` | Web Audio API / Speech recognition | Bottom sheet di atas riwayat chat asli (buang chat fiktif suhu 24°C/ventilasi), visualizer gelombang suara real-time, tombol Berhenti. |
| 17 | `17._kamera_rumah` (Terang/Gelap) | Ganti | `screens/tabs/cameras_tab.dart` | `GET /cameras`, `POST /cameras/{id}/privacy` | Banner privasi, grid 2 kolom kamera dengan thumbnail flat inset / stream nyata, status dot & metadata mono. |
| 18 | `18._live_view_kamera_rumah` | Ganti | `screens/camera_live_screen.dart` | `GET /cameras/{id}/whep`, `GET /cameras/{id}/snapshot`, `POST /cameras/{id}/privacy` | Pemutar live WebRTC/snapshot, label "Mode privasi" pada saklar, tab rekaman & kejadian. |
| 19 | `19._pemutar_rekaman_kamera_rumah` | Baru | `screens/recording_player_screen.dart` | `GET /cameras/recordings/{id}/playback`, `DELETE /cameras/recordings/{id}` | Placeholder datar inset + kamera ikon, tombol putar/jeda, loncat -10s/+10s, metadata mono, Simpan ke HP & konfirmasi Hapus. |
| 20 | `20._tambah_kamera_rumah` | Baru | `screens/add_camera_screen.dart` | `POST /cameras/pairing-code` | Alur pairing kamera HP bekas nyata: kode 6-digit mono, timer hitung mundur, tombol Salin kode & Buat kode baru. |
| 21 | `21._keluarga_ringkasan_rumah` | Ganti | `screens/family_summary_screen.dart` | `GET /family/summary`, `GET /family/events` | Hanya admin (chip "Hanya admin"), kartu metrik agregat riil: Waktu belajar, Aktif lewat tengah malam, Kejadian jatuh. Catatan kaki tanpa pengenalan wajah. |
| 22 | `22._detail_kejadian_keluarga_rumah` | Baru | `screens/family_event_detail_screen.dart` | `GET /family/events/{id}` | Jenis kejadian, kamera, waktu mono, durasi mono, klip/thumbnail resmi, tombol "Lihat rekaman". Buang identitas wajah/HP orang. |
| 23 | `23._lainnya_rumah` | Ganti | `screens/tabs/more_tab.dart` | `GET /auth/me`, `POST /auth/logout` | Tab ke-4 bottom nav: Profil pengguna & chip peran, menu Perangkat, Keluarga (admin), Notifikasi, Pengaturan, Keluar. Buang teks Raspberry Pi/OS/IP. |
| 24 | `24._notifikasi_rumah` | Baru | `screens/notifications_screen.dart` | `GET /audit/logs`, `GET /family/events` | Riwayat Hari Ini & Kemarin, dot 8px tanpa strip border kiri, jam mono, empty state "Belum ada notifikasi". |
| 25 | `25._pengaturan_sistem_rumah` | Ganti | `screens/settings_screen.dart` | `GET /auth/me`, `POST /auth/change-password`, `GET /health` | Satu kolom ringan: Akun (kata sandi, 2FA), Tampilan (Tema segmen Terang/Gelap/Sistem), Privasi, Anggota, Tentang (versi app & server). |
| 26 | `26._kelola_anggota_rumah` | Ganti | `screens/manage_members_screen.dart` | `GET /auth/users`, `POST /auth/users`, `PUT /auth/users/{id}`, `DELETE /auth/users/{id}` | Daftar anggota (nama, chip peran Public Sans, terakhir aktif), bottom sheet Tambah Anggota (username, sandi sementara, peran). |
| 27 | Shared Shell & Bottom Nav | Ganti | `screens/shell_screen.dart` + `components/app_bottom_nav.dart` | - | Satu komponen 4-tab (Beranda, Kamera, Asisten, Lainnya), tinggi 80px, pill aktif 64x32 tint ON, icon Fill aksen, tanpa border atas. |

---

## 2. Tabel Pemetaan Ikon (Material Symbols ke Phosphor Icons)

| Konteks UI | Material Symbol Mockup | Phosphor Icon (Regular 24px) | Phosphor Fill (Khusus Tab Aktif) |
|---|---|---|---|
| Tab Beranda | `home` | `PhosphorIcons.house()` | `PhosphorIconsFill.house` |
| Tab Kamera | `videocam` | `PhosphorIcons.videoCamera()` | `PhosphorIconsFill.videoCamera` |
| Tab Asisten | `mic` | `PhosphorIcons.microphone()` | `PhosphorIconsFill.microphone` |
| Tab Lainnya | `more_horiz` | `PhosphorIcons.dotsThree()` | `PhosphorIconsFill.dotsThree` |
| Notifikasi | `notifications` | `PhosphorIcons.bell()` | - |
| Tambah | `add` | `PhosphorIcons.plus()` | - |
| Kembali | `arrow_back` | `PhosphorIcons.arrowLeft()` | - |
| Tutup / Batal | `close` | `PhosphorIcons.x()` | - |
| Centang Sukses | `check_circle` / `check` | `PhosphorIcons.checkCircle()` | - |
| Peringatan / Bahaya | `warning` / `error` | `PhosphorIcons.warningCircle()` / `warning()` | - |
| Lampu | `lightbulb` | `PhosphorIcons.lightbulb()` | - |
| Kipas Angin | `mode_fan` | `PhosphorIcons.fan()` | - |
| Sirine / Alarm | `security` / `alarm` | `PhosphorIcons.bellRinging()` / `shield()` | - |
| Sensor Gas MQ-2 | `gas_meter` / `sensors` | `PhosphorIcons.gauge()` | - |
| Sensor Cahaya LDR | `wb_sunny` / `light_mode` | `PhosphorIcons.sun()` | - |
| Sinyal WiFi | `wifi` | `PhosphorIcons.wifiHigh()` / `wifiSlash()` | - |
| Privasi Kamera | `visibility_off` | `PhosphorIcons.eyeSlash()` | - |
| Putar Video | `play_arrow` | `PhosphorIcons.play()` | `PhosphorIconsFill.play` |
| Jeda Video | `pause` | `PhosphorIcons.pause()` | `PhosphorIconsFill.pause` |
| Mundur 10s | `replay_10` | `PhosphorIcons.arrowCounterClockwise()` | - |
| Maju 10s | `forward_10` | `PhosphorIcons.arrowClockwise()` | - |
| Simpan / Unduh | `download` | `PhosphorIcons.downloadSimple()` | - |
| Hapus | `delete` | `PhosphorIcons.trash()` | - |
| Salin Kode | `content_copy` | `PhosphorIcons.copy()` | - |
| Scan QR | `qr_code_scanner` | `PhosphorIcons.qrCode()` / `scan()` | - |
| Kelola Anggota | `group` | `PhosphorIcons.users()` | - |
| Pengaturan | `settings` | `PhosphorIcons.gear()` | - |
| Keluar Akun | `logout` | `PhosphorIcons.signOut()` | - |
| Modul ESP32 | `memory` | `PhosphorIcons.cpu()` | - |

*(Catatan: Sesuai aturan, TIDAK ADA ikon sparkle, tongkat ajaib, atau bintang AI di seluruh aplikasi).*

---

## 3. Sumber Font & Lisensi Resmi

- **Public Sans**: Lisensi SIL Open Font License 1.1 (OFL). Sumber: United States Web Design System (USWDS) / Google Fonts (`https://github.com/uswds/public-sans`).
- **IBM Plex Mono**: Lisensi SIL Open Font License 1.1 (OFL). Sumber: IBM / Google Fonts (`https://github.com/google/fonts/tree/main/ofl/ibmplexmono`).
- Kedua font disimpan secara offline di `app/assets/fonts/` dan didaftarkan pada `app/pubspec.yaml`. Tidak ada fetch jaringan runtime `google_fonts`.
