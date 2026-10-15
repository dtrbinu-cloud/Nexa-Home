# Panduan Konfigurasi Google OAuth2 & Layanan Email SMTP

Panduan 10 langkah ringkas untuk mengaktifkan **Login Google** pada domain `https://aujasena.my.id` dan **Layanan Pengiriman Email OTP / QR Code** menggunakan Gmail App Password.

---

### Bagian A: Menyiapkan Google OAuth 2.0 (Langkah 1 - 5)

1. **Buka Google Cloud Console:**
   Kunjungi [Google Cloud Console](https://console.cloud.google.com/) dan buat project baru (misalnya: `Nexa Home`).

2. **Konfigurasi Layanan OAuth Consent Screen:**
   - Masuk ke menu **APIs & Services** > **OAuth consent screen**.
   - Pilih User Type **External**, lalu klik **Create**.
   - Isi Nama Aplikasi (`Nexa Home`), Email Dukungan, dan Developer Contact Information.
   - Pada bagian **Authorized domains**, tambahkan: `aujasena.my.id`. Simpan dan lanjutkan.

3. **Buat Kredensial OAuth 2.0 Client ID:**
   - Masuk ke menu **APIs & Services** > **Credentials** > **+ Create Credentials** > **OAuth client ID**.
   - Pilih Application type: **Web application**.
   - Isi Nama: `Nexa Home Web & Mobile Client`.

4. **Isi Authorized JavaScript Origins & Redirect URIs:**
   - **Authorized JavaScript origins:**
     - `https://aujasena.my.id`
     - `http://localhost:5173` *(opsional untuk pengujian dev lokal)*
   - **Authorized redirect URIs:**
     - `https://aujasena.my.id/api/auth/google/callback`
     - `https://aujasena.my.id/login`
     - `http://localhost:5173/login` *(opsional untuk dev)*

5. **Salin Client ID & Client Secret:**
   - Setelah disimpan, Google akan menampilkan modal berisi **Client ID** (akhiran `.apps.googleusercontent.com`) dan **Client Secret**.
   - Simpan kedua kunci ini untuk langkah 9.

---

### Bagian B: Menyiapkan Gmail App Password SMTP (Langkah 6 - 8)

6. **Aktifkan Verifikasi 2 Langkah Akun Google:**
   - Buka [Google Account Security](https://myaccount.google.com/security).
   - Pastikan **2-Step Verification** (Verifikasi 2 Langkah) sudah berstatus **Aktif (On)**.

7. **Buat Sandi Aplikasi (App Password):**
   - Cari menu **App passwords** (atau buka [Google App Passwords](https://myaccount.google.com/apppasswords)).
   - Masukkan nama aplikasi: `Nexa Home Server`, lalu klik **Create**.

8. **Salin 16-Digit Sandi Aplikasi:**
   - Google akan memberikan kode 16 karakter tanpa spasi (misalnya: `abcd efgh ijkl mnop`).
   - Salin kode tersebut sebagai `SMTP_PASSWORD`.

---

### Bagian C: Memasukkan ke `.env` & Verifikasi (Langkah 9 - 10)

9. **Perbarui Berkas `.env`:**
   Buka file `.env` di direktori proyek dan lengkapi variabel berikut:
   ```env
   # Google OAuth2
   GOOGLE_CLIENT_ID=xxxxxxxxxxxx-xxxxxxxxxxxxxxxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx

   # Layanan Email SMTP
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=email.anda@gmail.com
   SMTP_PASSWORD=abcdefghijklmnop
   SMTP_FROM=Nexa Home <email.anda@gmail.com>
   SMTP_TLS=true
   SMTP_SSL=false
   ```
   > **Catatan Dev / Fallback:** Jika variabel SMTP dikosongkan saat proses pengembangan, server tetap berfungsi normal dan akan mencetak kode OTP serta data QR Code secara rapi langsung di terminal konsol server.

10. **Jalankan & Uji Coba Fitur Akun:**
    - Masuk ke `https://aujasena.my.id/login`
    - Coba tab **"Daftar Akun Baru"** untuk registrasi mandiri.
    - Coba tombol **"Lanjutkan dengan Google"** untuk masuk instan dengan akun Google.
    - Coba tautkan akun di menu **Pengaturan > Profil & Penautan Akun**.
    - Coba tombol **"Lupa Kata Sandi?"** untuk memverifikasi penerimaan kode OTP 6 digit.
