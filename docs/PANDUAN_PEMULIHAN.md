# Panduan Pemulihan Bencana, Backup, Restore & Rotasi Kunci

Dokumen ini memuat prosedur operasional standar (*Standard Operating Procedure / SOP*) untuk mencadangkan data, memulihkan sistem dari kegagalan (*disaster recovery*), merotasi kunci enkripsi, dan memindahkan server Nexa Home ke komputer baru.

---

## 1. Prosedur Pencadangan Sistem (Backup)

Nexa Home menggunakan basis data SQLite dalam mode **Write-Ahead Logging (WAL)**. Untuk mencegah korupsi data saat server sedang sibuk melayani transaksi, pencadangan **wajib** menggunakan SQLite Online Backup API yang telah terintegrasi di dalam skrip `scripts/backup.ps1`.

### Cara Membuat Cadangan:
Buka PowerShell di folder proyek dan jalankan:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\backup.ps1
```

### Parameter Tambahan:
* `-OutputDir <folder>` : Menentukan folder penyimpanan (default: `backups/`).
* `-IncludeClips $false` : Hanya mencadangkan database dan konfigurasi tanpa klip rekaman video (ukuran arsip jauh lebih kecil).

### Struktur Berkas Arsip Cadangan:
Setiap kali skrip dijalankan, akan tercipta 2 berkas di dalam folder `backups/`:
1. `nexa_backup_YYYYMMDD_HHMMSS.zip` — Arsip kompresi berisi database `rumah.db`, berkas `.env`, konfigurasi tunnel, dan rekaman klip terenkripsi.
2. `nexa_backup_YYYYMMDD_HHMMSS.zip.sha256` — Berkas teks berisi checksum hash SHA-256 untuk memvalidasi bahwa berkas cadangan tidak pernah korup atau dimodifikasi.

---

## 2. Prosedur Pemulihan Sistem (Restore)

Skrip pemulihan secara otomatis melakukan:
1. Pengecekan checksum SHA-256.
2. Pembuatan **Rollback Snapshot Darurat** ke folder `server/data/rollback_before_restore/` sebelum menimpa data aktif.
3. Ekstraksi arsip dan verifikasi integritas database (`PRAGMA integrity_check`).
4. Penerapan database atomik via SQLite Online Backup API (aman bahkan jika backend sedang melayani request).

### Cara Memulihkan dari Cadangan Terbaru:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\restore.ps1
```
Skrip akan otomatis mencari arsip `.zip` paling baru di dalam folder `backups/` dan meminta konfirmasi pengetikan kata `"YA"`.

### Cara Memulihkan dari Berkas Tertentu (Tanpa Prompt Konfirmasi):
```powershell
powershell -ExecutionPolicy Bypass -File scripts\restore.ps1 -BackupFile "backups\nexa_backup_20261014_165815.zip" -Force
```

---

## 3. Prosedur Rotasi Kunci Enkripsi Data Diam (Key Rotation)

Rekaman video gerakan dan data sensitif dienkripsi menggunakan algoritma **AES-256-GCM** dengan kunci simetris `MEDIA_ENCRYPTION_KEY` di dalam `.env`. Disarankan merotasi kunci ini setiap 6–12 bulan atau saat ada indikasi kebocoran kredensial.

Skrip `scripts/rotate-keys.py` akan mendekripsi seluruh rekaman lama menggunakan kunci lama, mengacak nonce 12-byte baru, mengenkripsi ulang dengan kunci baru, memperbarui entri database, dan memperbarui baris `MEDIA_ENCRYPTION_KEY` di file `.env`.

### Langkah 1: Uji Simulasi Terlebih Dahulu (Dry-Run)
Pastikan seluruh klip dapat didekripsi tanpa merusak data apa pun:
```powershell
server\.venv\Scripts\python.exe scripts\rotate-keys.py --generate-key --dry-run
```
Periksa ringkasan di konsol; pastikan `Gagal: 0`.

### Langkah 2: Jalankan Rotasi Penuh
```powershell
server\.venv\Scripts\python.exe scripts\rotate-keys.py --generate-key
```
Skrip akan mencatat kunci baru, memperbarui `.env`, dan membuat file cadangan `.env.bak` secara otomatis.

---

## 4. Panduan Pemindahan Server PC / Instal Ulang Windows 10

Jika Anda ingin memindahkan Nexa Home ke PC lain atau setelah instal ulang Windows 10, ikuti 6 langkah mudah berikut:

### Langkah 1: Buat Arsip di PC Lama
Di PC lama, jalankan:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\backup.ps1
```
Salin berkas `nexa_backup_*.zip` dan `nexa_backup_*.zip.sha256` ke Flashdisk atau Google Drive Anda.

### Langkah 2: Siapkan Lingkungan di PC Baru
Pastikan PC baru terhubung ke internet dan telah terpasang:
1. **Git for Windows** ([git-scm.com](https://git-scm.com))
2. **Python 3.11** (centang opsi *"Add Python to PATH"* saat instalasi).

### Langkah 3: Unduh Proyek & Jalankan Setup
Buka PowerShell di PC baru:
```powershell
cd C:\Users\<NamaUser>\Downloads
git clone <URL_REPOSITORY_ANDA> "Nexa Home"
cd "Nexa Home"
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```
Skrip setup akan otomatis menyiapkan virtual environment Python, mengunduh seluruh dependensi, dan menyiapkan build frontend.

### Langkah 4: Terapkan Arsip Cadangan
Salin berkas backup dari flashdisk ke folder `backups/`, lalu jalankan:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\restore.ps1 -Force -RestoreEnv
```
Seluruh riwayat database, perangkat yang telah terhubung, akun anggota keluarga, dan kredensial tunnel akan langsung kembali ke status semula!

### Langkah 5: Pasang Auto-Start Layanan
Agar seluruh layanan menyala otomatis setiap kali PC baru dihidupkan:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-autostart.ps1
```

### Langkah 6: Verifikasi Kesiapan Sistem
Jalankan watchdog satu kali untuk memverifikasi bahwa seluruh port dan endpoint berfungsi:
```powershell
server\.venv\Scripts\python.exe scripts\watchdog.py --once
```
Jika seluruh indikator berstatus `[OK] AKTIF`, proses pemindahan server selesai 100%!
