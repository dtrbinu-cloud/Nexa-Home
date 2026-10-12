# Proyek "Rumah" — Smart Home + Asisten AI + Pengawasan Keluarga

Dokumen ini berisi (A) keputusan arsitektur dan (B) prompt untuk AI agent (Antigravity).
Tempel bagian B ke agent. Kerjakan SATU tahap per sesi, jangan sekaligus.

---

# A. KEPUTUSAN ARSITEKTUR (ringkas)

## Realita hardware server
i3 gen 4 (2 core/4 thread), RAM 8 GB, tanpa GPU, Windows 10.
Artinya:
- Jangan analisis semua frame semua kamera. Pakai motion trigger + 2–5 FPS + resolusi 640px.
- Maksimal 2–3 kamera aktif analisis. Kamera lain hanya streaming/rekam.
- Model AI harus kecil dan dijalankan lewat ONNX Runtime (CPU).
- Model besar (LLM, vision berat) lewat API, bukan lokal.

## Komponen
| Bagian | Pilihan | Alasan |
|---|---|---|
| Backend utama | Python FastAPI + SQLite (WAL) | Satu bahasa dengan AI worker, ringan di RAM 8 GB |
| Pesan realtime ke ESP | MQTT (Mosquitto lokal + opsional HiveMQ cloud) | Lebih stabil dari HTTP polling di kode lama |
| Stream kamera | MediaMTX (RTSP/WebRTC/HLS) | Satu binary, ringan, jalan di Windows |
| Frontend | Web app PWA (SvelteKit atau React+Vite), bisa dipasang di HP | Satu codebase untuk web dan "app" |
| Akses dari luar | Tailscale atau Cloudflare Tunnel | Tanpa buka port router |
| Deteksi orang/pose | YOLO11n-pose (ONNX, int8) | Satu model: orang + 17 titik tubuh, cukup cepat di CPU |
| Deteksi benda | YOLO11n (COCO) untuk kelas umum | HP, remote, tas, botol, laptop, buku, dll |
| Cari barang "kunci/dompet" | Log deteksi + snapshot; pencarian lanjutan lewat vision API hanya saat diminta | COCO tidak punya kelas kunci/dompet; model open-vocab terlalu berat untuk i3 |
| Kenali anggota keluarga | InsightFace (buffalo_s) opsional, dengan persetujuan | Untuk statistik per orang |
| LLM asisten | DeepSeek via API (function calling) | Nama model persis dibuat konfigurable, cek di dokumentasi DeepSeek |
| STT (suara → teks) | Web Speech API di browser dulu; faster-whisper "base" sebagai fallback | Gratis dan ringan |
| TTS (teks → suara) | Lihat bagian di bawah | |

## Jawaban: TTS pakai API atau model sendiri?
Rekomendasi: **hybrid, dengan API/online sebagai default dan model lokal sebagai cadangan.**
1. Default: `edge-tts` (suara Microsoft Edge, ada id-ID-ArdiNeural / GadisNeural, gratis, natural, jalan di CPU karena proses di cloud). Catatan: tidak resmi, bisa berubah sewaktu-waktu.
2. Cadangan offline: **Piper TTS** (ONNX, sangat ringan, realtime di i3, kualitas cukup bagus, ada voice Indonesia).
3. Opsi berbayar kalau mau paling natural dan stabil: Google Cloud TTS, ElevenLabs, atau OpenAI TTS (lewat satu antarmuka provider supaya mudah ganti).
Model TTS neural besar (XTTS, F5-TTS, dll) tidak disarankan di i3 tanpa GPU: lambat (beberapa detik per kalimat).

## Privasi dan keamanan (wajib, bukan opsional)
- Semua video diproses lokal. Tidak ada frame yang dikirim ke internet kecuali pencarian barang yang diaktifkan manual, dan itu per snapshot.
- Kamera hanya di area umum rumah. Jangan kamar mandi/kamar tidur privat.
- Anggota keluarga tahu ada kamera. Beri indikator di app dan jadwal "mode privasi" per kamera.
- Fitur pengawasan anak/kesehatan hanya terlihat oleh akun orang tua (admin).
- Rekaman dienkripsi saat disimpan, retensi otomatis (misal 7 hari video, 90 hari statistik).
- Yang disimpan untuk insight adalah angka/kejadian (durasi belajar, jam keluar), bukan video.
- Fitur kesehatan = pengingat dan deteksi kejadian (jatuh, tidak bergerak lama). Bukan diagnosis medis.

## Perbaikan yang perlu dilakukan dari kode ESP lama
- Rahasia (WiFi, MQTT password, DEVICE_KEY) tertulis langsung di file. **Ganti semuanya sekarang** karena sudah terlanjur terbagi/ter-upload, lalu pindahkan ke `secrets.py` yang tidak masuk git.
- Pakai MQTT sebagai transport utama, HTTP polling hanya fallback.
- Tambah pin untuk kipas (atau pakai relay yang ada) dan beri nama perintah yang konsisten.
- Perintah dibuat berbentuk JSON `{device, channel, action}` supaya mudah ditambah, bukan banyak `if cmd == ...`.

## Desain UI (anti tampilan "AI banget")
Hindari: gradien ungu-biru, glassmorphism, efek glow, emoji sebagai ikon, font Inter, kartu bayangan tebal, sudut sangat bulat, teks "✨".

Token desain (simpan di SATU file, dilarang hardcode warna di komponen):
- Font teks: **Public Sans**. Angka sensor/log: **IBM Plex Mono**. Hanya dua font ini.
- Ikon: **Phosphor Icons** gaya Regular, ukuran 20/24 saja. Satu set ikon, tidak campur.
- Mode terang: background `#F4F1EA`, surface `#FBF9F4`, garis `#D9D3C6`, teks `#1F2421`, teks sekunder `#5E655F`
- Aksen tunggal (hijau tua): `#2F6B5B`, hover `#255849`
- Status: aman `#4C7A3F`, peringatan `#B7791F`, bahaya `#B23A2E`
- Mode gelap: background `#151816`, surface `#1D211E`, garis `#2D332F`, teks `#E8E6DF`, aksen `#5FA08E`
- Radius 6px (kecil) dan 10px (kartu). Tanpa bayangan; pakai garis 1px. Tanpa gradien.
- Grid spasi 4/8/12/16/24/32. Tinggi tombol 40px. Ukuran teks: 13/15/18/24/32.
- Bahasa UI: Indonesia, nada singkat dan datar ("Lampu ruang tengah dinyalakan"), bukan ceria berlebihan.

---

# B. PROMPT UNTUK AI AGENT

Salin dari garis ini sampai akhir file.

---

## PERAN
Kamu adalah engineer senior full-stack + IoT + computer vision. Kamu membangun sistem smart home bernama "Rumah" dari nol, secara bertahap. Pemilik proyek: Risang. Bahasa komunikasi denganku: Indonesia. Bahasa kode dan nama variabel: Inggris.

## ATURAN KERJA (berlaku di semua tahap)
1. Kerjakan HANYA satu tahap per giliran. Setelah selesai, berhenti, tampilkan ringkasan, cara menjalankan, dan hasil uji, lalu tunggu aku bilang "lanjut".
2. Sebelum menulis kode tiap tahap, tulis rencana singkat (file yang dibuat, keputusan penting). Kalau ada keputusan yang tidak bisa dibatalkan atau ambigu, tanya dulu.
3. Setiap tahap harus bisa dijalankan dan diuji sendiri. Sertakan tes otomatis untuk logika penting dan skrip demo.
4. Jangan menaruh rahasia di kode. Semua lewat file `.env` / `secrets` yang masuk `.gitignore`. Sediakan `.env.example`.
5. Jangan menambah fitur di luar tahap yang sedang dikerjakan.
6. Semua teks UI dalam bahasa Indonesia. Semua konfigurasi (nama model, ambang batas, retensi) bisa diubah lewat file config, bukan hardcode.
7. Jaga komentar dan README tetap singkat dan jujur. Tulis apa yang belum teruji.
8. Target lingkungan server: Windows 10, i3 gen 4, RAM 8 GB, tanpa GPU. Setiap model AI harus diuji beban CPU dan RAM-nya dan hasilnya dilaporkan. Jika terlalu berat, turunkan FPS/resolusi atau ganti model yang lebih kecil, jangan diam-diam.

## TUMPUKAN TEKNOLOGI (jangan ganti tanpa tanya)
- Backend: Python 3.11, FastAPI, SQLite (mode WAL), SQLAlchemy, WebSocket
- Pesan perangkat: MQTT (Mosquitto lokal, broker bisa diganti HiveMQ lewat config)
- Stream kamera: MediaMTX
- Frontend: web app PWA (SvelteKit atau React + Vite, pilih satu dan tulis alasannya), responsif, bisa dipasang di HP
- AI vision: ONNX Runtime CPU, YOLO11n-pose dan YOLO11n (versi int8 jika bisa)
- LLM: DeepSeek lewat API dengan function calling; nama model dari config
- TTS: antarmuka `TTSProvider` dengan dua implementasi: `edge-tts` (default) dan `piper` (offline)
- STT: Web Speech API di browser; fallback `faster-whisper` base
- Akses luar: dokumentasikan setup Tailscale atau Cloudflare Tunnel (tanpa buka port)

## SISTEM DESAIN (WAJIB KONSISTEN)
Buat `design-tokens` (CSS variables + file JSON) di tahap 1 dan pakai di SEMUA layar. Dilarang hardcode warna, ukuran font, radius, atau spasi di komponen. Sebelum menyelesaikan tiap tahap, jalankan pemeriksaan otomatis (grep/lint) yang gagal bila ada warna hex di luar file token.

- Font: Public Sans (teks), IBM Plex Mono (angka sensor dan log). Tidak ada font lain.
- Ikon: Phosphor Icons Regular, 20px dan 24px. Dilarang emoji sebagai ikon, dilarang campur set ikon.
- Terang: bg `#F4F1EA`, surface `#FBF9F4`, border `#D9D3C6`, teks `#1F2421`, teks-2 `#5E655F`
- Aksen tunggal: `#2F6B5B` (hover `#255849`). Tidak ada aksen kedua.
- Status: ok `#4C7A3F`, warn `#B7791F`, danger `#B23A2E`
- Gelap: bg `#151816`, surface `#1D211E`, border `#2D332F`, teks `#E8E6DF`, aksen `#5FA08E`
- Radius 6px / 10px. Tanpa bayangan, tanpa gradien, tanpa glow, tanpa glassmorphism. Pemisah pakai border 1px.
- Spasi kelipatan 4. Tinggi tombol dan input 40px. Skala teks 13/15/18/24/32.
- Komponen dasar dibuat sekali (Button, Card, Switch, Badge, Input, Modal, Toast, EmptyState) dan dipakai ulang. Tidak boleh ada gaya tombol baru di layar lain.
- Gaya bahasa: singkat, datar, informatif. Contoh: "Lampu kamar dimatikan", bukan "Yay! Lampu sudah mati ✨".
- Ada halaman `/design` yang menampilkan semua token dan komponen sebagai rujukan, supaya konsistensi mudah dicek.

## KONTEKS PERANGKAT ESP32 YANG SUDAH ADA
Firmware MicroPython lama punya: 3 lampu (tengah pin 21, dapur/tamu pin 17, kamar pin 16), buzzer pin 19, relay pin 32 (aktif LOW), sensor gas MQ2 pin 33 (alarm di raw >= 1500), sensor cahaya LDR pin 22. Perintah lama: `on`, `off`, `lamp_on/off`, `lamp_tengah_on/off`, `lamp_dapur_tamu_on/off`, `lamp_kamar_on/off`, `relay_on/off`. Status yang dikirim: state lampu/relay, gas_raw/gas_pct/gas_alarm, ldr, is_dark, ip, uptime. Pertahankan kemampuan ini, tapi rancang ulang protokolnya (lihat Tahap 2). File kode lama akan kuberikan sebagai referensi.

---

## TAHAP 0 — Fondasi repo dan keputusan
Tujuan: struktur proyek, tooling, dokumen keputusan.
- Monorepo: `server/`, `web/`, `firmware/`, `camera-app/`, `docs/`.
- `docs/DECISIONS.md`: pilihan framework frontend dan alasannya, skema topik MQTT, skema database awal.
- Skrip `scripts/dev.ps1` untuk menjalankan semua layanan di Windows.
- `.gitignore`, `.env.example`, aturan lint dan format.
Selesai jika: `dev.ps1` menjalankan backend kosong dan frontend kosong, README menjelaskan langkahnya.

## TAHAP 1 — Backend inti, autentikasi, shell UI
- FastAPI dengan SQLite WAL, migrasi, endpoint kesehatan.
- Pengguna dan peran: `admin` (orang tua), `member`, `child`. Login dengan password (argon2) + JWT berumur pendek + refresh token. Siapkan TOTP 2FA untuk admin.
- Log audit: siapa melakukan apa dan kapan.
- Frontend: halaman login, navigasi (Beranda, Perangkat, Asisten, Kamera, Keluarga, Pengaturan), mode terang/gelap, halaman `/design`, semua dari token.
Selesai jika: login jalan, role dicek di backend (bukan hanya disembunyikan di UI), tes otomatis untuk autentikasi, tidak ada warna di luar token.

## TAHAP 2 — Kontrol IoT (MQTT) dan firmware baru
- Skema topik: `home/{device_id}/cmd`, `/state`, `/event`, `/availability` (LWT). Payload JSON `{channel, action, id}`.
- Registri perangkat dan kanal di database (lampu, kipas, relay, sensor). Menambah kanal tidak perlu ubah kode.
- Firmware MicroPython baru: rahasia di `secrets.py`, reconnect otomatis, tidak memblokir saat `beep`, gas alarm tetap bekerja walaupun jaringan putus, status dikirim saat berubah dan berkala.
- Autentikasi per perangkat (user/password MQTT per device, ACL topik).
- UI Perangkat: saklar per kanal, status online/offline, nilai sensor gas dan cahaya dengan IBM Plex Mono, riwayat grafik sederhana.
- Aturan otomasi sederhana (jika gelap dan ada orang di ruang X, nyalakan lampu X; jika gas alarm, kirim notifikasi) disimpan di database.
Selesai jika: ESP (atau simulator perangkat bila ESP tidak tersedia) bisa dikontrol dari UI, status realtime lewat WebSocket, perangkat offline terdeteksi, ada tes untuk parser perintah.

## TAHAP 3 — Asisten percakapan dan suara
- Layanan LLM dengan function calling ke DeepSeek (nama model dan base URL dari config). Alat (tools) yang dibuka ke asisten: `control_device`, `get_device_states`, `get_sensor_readings`, `find_item` (stub dulu), `get_family_summary` (stub, hanya untuk admin).
- Konfirmasi untuk aksi sensitif, dan semua pemanggilan alat dicatat di audit log.
- Riwayat percakapan per pengguna, batas panjang konteks.
- Suara: `TTSProvider` (edge-tts default, piper offline), cache audio untuk kalimat umum. Input suara lewat Web Speech API, fallback faster-whisper.
- UI Asisten: chat + tombol mikrofon + indikator "sedang bicara", dengan komponen dasar dari token.
- Kepribadian asisten: bahasa Indonesia, singkat, tidak sok akrab. Tulis di `server/prompts/assistant.md`.
- Batasi akses: akun `child` tidak bisa memerintah alat berisiko (misal relay utama) dan tidak bisa melihat data keluarga.
Selesai jika: "nyalakan lampu kamar" dan "kipas mati" lewat chat dan suara benar-benar mengubah perangkat; ada tes untuk pemetaan perintah; waktu respons TTS dilaporkan.

## TAHAP 4 — Kamera dari HP bekas
- Aplikasi kamera: mulai sebagai PWA satu halaman (buka di HP bekas, pilih nama ruangan, tombol mulai) yang mengirim video lewat WebRTC (WHIP) ke MediaMTX. Dokumentasikan opsi lanjut jadi aplikasi Android native (Kotlin CameraX + RTSP) bila PWA kurang stabil.
- Pairing aman: kode sekali pakai dari app admin, token per kamera yang bisa dicabut.
- Fitur untuk HP bekas: layar tetap menyala (wake lock), mode hemat baterai, auto-reconnect, indikator kamera aktif yang terlihat di ruangan.
- Rekam hanya saat ada gerakan (motion trigger), simpan terenkripsi, retensi otomatis lewat config. Pengaturan "mode privasi" per kamera dan per jadwal.
- UI Kamera: grid live view, daftar kejadian, pemutaran klip.
Selesai jika: minimal 2 HP terhubung, live view di web, klip gerakan tersimpan dan terhapus otomatis sesuai retensi, token kamera bisa dicabut, beban CPU/RAM server dilaporkan.

## TAHAP 5 — Vision AI dan pencarian barang
- Worker terpisah (proses sendiri) membaca stream pada 2–5 FPS, 640px, hanya saat ada gerakan atau orang. Antrean dengan batas, buang frame lama bila beban tinggi (jangan menumpuk).
- YOLO11n-pose (orang + pose) dan YOLO11n (benda) via ONNX Runtime. Bandingkan beberapa varian dan laporkan akurasi vs kecepatan di mesin ini; pilih yang paling akurat yang masih ≥ 2 FPS per kamera aktif.
- Pelacakan antar frame (ByteTrack atau sejenis) supaya satu orang tidak terhitung berulang.
- Log benda: kelas, kamera/ruangan, waktu, posisi, thumbnail kecil. Dedup agar database tidak membengkak.
- `find_item`: (1) cari di log benda terakhir dilihat, jawab "terakhir terlihat di ruang tamu, di meja, 14.32"; (2) opsional, bila diaktifkan admin, kirim beberapa snapshot relevan ke vision API untuk benda di luar COCO (kunci, dompet), dengan peringatan jelas dan toggle per kamera.
- Hubungkan ke asisten: "di mana HP-ku?" memanggil `find_item`.
Selesai jika: benda COCO bisa dicari lewat chat, ada laporan benchmark (FPS, CPU, RAM, akurasi uji manual pada rekaman contoh), dan worker tidak membuat server hang saat beban tinggi.

## TAHAP 6 — Insight keluarga (hanya admin, dengan persetujuan)
- Pengenalan anggota keluarga: opsional. Pendaftaran wajah hanya oleh admin dengan persetujuan yang tercatat. Jika dimatikan, statistik dibuat per ruangan, bukan per orang.
- Aturan dan data yang disimpan adalah kejadian dan angka, bukan video:
  - Peringatan bahaya: jatuh (pose), anak di area berbahaya (dapur saat kompor/gas), tidak bergerak lama.
  - Pemakaian HP larut malam: orang + HP terdeteksi di jam yang diatur (misal setelah 23.00) → notifikasi ke orang tua.
  - Durasi belajar: orang duduk di "zona belajar" yang digambar admin di layar kamera, dengan buku/laptop → total harian dan mingguan.
  - Waktu di rumah vs keluar: dari kehadiran terakhir di semua kamera + opsi lokasi dari HP (izin eksplisit). Hitung "hari berturut-turut di rumah".
  - Rutinitas sehat: jika seseorang di rumah ≥ 4 hari berturut-turut, asisten menyarankan keluar rumah, olahraga, atau jalan-jalan (pesan lembut, bukan menyuruh keras, bisa disnooze).
- Semua aturan dan ambang batas bisa diubah admin di UI. Setiap fitur punya saklar aktif/nonaktif.
- Ringkasan harian dan mingguan, bisa diminta lewat asisten.
- Wajib: banner jelas di UI bahwa ini bukan alat medis; tidak ada diagnosis.
- UI Keluarga: kartu per orang atau per ruangan, grafik sederhana (garis dan batang, warna dari token, tanpa dekorasi).
Selesai jika: tiap fitur punya tes dengan rekaman contoh, saklar bekerja, akun non-admin tidak bisa mengakses endpoint ini (diuji), dan data yang disimpan hanya angka/kejadian.

## TAHAP 7 — Pengerasan keamanan dan peluncuran
- Semua layanan hanya di jaringan lokal; akses luar via Tailscale/Cloudflare Tunnel. TLS di mana-mana.
- Enkripsi data diam untuk rekaman dan database sensitif, rotasi kunci, skrip backup dan restore yang diuji.
- Rate limit login, kunci akun setelah gagal berulang, notifikasi login baru.
- Pemeriksaan keamanan: dependensi rentan, header, CORS ketat, validasi input, uji dasar akses antar peran.
- Auto-start layanan di Windows (NSSM atau Task Scheduler), pemantauan kesehatan layanan, log berputar.
- Dokumentasi: panduan pemakaian untuk keluarga, panduan pasang kamera, panduan pemulihan.
Selesai jika: daftar periksa keamanan terisi, uji restore berhasil, server hidup ulang otomatis setelah reboot.

## FORMAT LAPORAN SETIAP TAHAP
1. Apa yang dibangun (maks 10 baris)
2. Cara menjalankan dan menguji
3. Hasil uji dan angka beban (CPU/RAM/FPS bila relevan)
4. Hal yang belum selesai atau berisiko
5. Pertanyaan untuk keputusanku sebelum tahap berikutnya
