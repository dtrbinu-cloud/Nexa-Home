#!/usr/bin/env python3
"""
scripts/generate_ui_comparison.py
Membuat lembar perbandingan berdampingan (Side-by-Side):
- Sisi Kiri: screen.png dari Google Stitch
- Sisi Kanan: hasil golden rendering dari app Flutter
Disimpan ke docs/ui-review/mobile/compare/
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = Path(__file__).resolve().parent.parent
STITCH_DIR = ROOT_DIR / "stitch_rumah_smart_home_ui"
GOLDEN_DIR = ROOT_DIR / "docs" / "ui-review" / "mobile"
COMPARE_DIR = GOLDEN_DIR / "compare"

PAIRS = [
    ("01_login", "1._login_rumah/screen.png", "screen_01_login_light_360.png", "Layar 1: Login"),
    ("02_verifikasi_2fa", "2._kode_verifikasi_rumah/screen.png", "screen_02_verify_2fa_light_360.png", "Layar 2: Verifikasi 2FA"),
    ("03_beranda_terang", "3._beranda_rumah/screen.png", "screen_03_beranda_light_360.png", "Layar 3: Beranda (Terang)"),
    ("03_beranda_gelap", "3._beranda_mode_gelap_rumah/screen.png", "screen_03_beranda_dark_360.png", "Layar 3: Beranda (Gelap)"),
    ("04_beranda_bahaya", "4._beranda_bahaya_rumah/screen.png", "screen_04_beranda_bahaya_light_360.png", "Layar 4: Beranda Bahaya"),
    ("05_semua_perangkat", "5._semua_perangkat_rumah/screen.png", "screen_05_semua_perangkat_light_360.png", "Layar 5: Semua Perangkat"),
    ("06_detail_perangkat", "6._detail_perangkat_lampu_rumah/screen.png", "screen_06_detail_perangkat_light_360.png", "Layar 6: Detail Perangkat"),
    ("07_pilih_jenis", "7._tambah_perangkat_pilih_jenis_rumah/screen.png", "screen_07_pilih_jenis_light_360.png", "Layar 7: Pilih Jenis Perangkat"),
    ("08_langkah_1_kode", "8._langkah_1_kode_pairing_rumah/screen.png", "screen_08_langkah_1_kode_light_360.png", "Layar 8: Langkah 1 Kode Pairing"),
    ("09_langkah_2_wifi", "9._langkah_2_sambung_wifi_alat_rumah/screen.png", "screen_09_langkah_2_wifi_light_360.png", "Layar 9: Langkah 2 Sambung WiFi Alat"),
    ("10_scan_qr", "10._scan_qr_rumah/screen.png", "screen_10_scan_qr_light_360.png", "Layar 10: Scan QR"),
    ("11_setup_wifi", "11._langkah_3_setup_wifi_rumah_rumah/screen.png", "screen_11_setup_wifi_light_360.png", "Layar 11: Langkah 3 Setup WiFi"),
    ("12_langkah_4_menghubungkan", "12._langkah_4_menghubungkan_rumah/screen.png", "screen_12_langkah_4_menghubungkan_light_360.png", "Layar 12: Langkah 4 Menghubungkan"),
    ("13_berhasil", "13._berhasil_tambah_perangkat_rumah/screen.png", "screen_13_berhasil_light_360.png", "Layar 13: Berhasil Tambah Perangkat"),
    ("14_gagal", "14._gagal_tambah_perangkat_rumah/screen.png", "screen_14_gagal_light_360.png", "Layar 14: Gagal Tambah Perangkat"),
    ("15_asisten_terang", "15._asisten_rumah/screen.png", "screen_15_asisten_light_360.png", "Layar 15: Asisten (Terang)"),
    ("15_asisten_gelap", "15._asisten_mode_gelap_rumah/screen.png", "screen_15_asisten_dark_360.png", "Layar 15: Asisten (Gelap)"),
    ("16_asisten_mendengarkan", "16._asisten_mendengarkan_rumah/screen.png", "screen_16_asisten_mendengarkan_light_360.png", "Layar 16: Asisten Mendengarkan"),
    ("17_kamera", "17._kamera_rumah/screen.png", "screen_17_kamera_light_360.png", "Layar 17: Tab Kamera"),
    ("18_live_view", "18._live_view_kamera_rumah/screen.png", "screen_18_live_view_light_360.png", "Layar 18: Live View Kamera"),
    ("19_pemutar_rekaman", "19._pemutar_rekaman_kamera_rumah/screen.png", "screen_19_pemutar_rekaman_light_360.png", "Layar 19: Pemutar Rekaman"),
    ("20_tambah_kamera", "20._tambah_kamera_rumah/screen.png", "screen_20_tambah_kamera_light_360.png", "Layar 20: Tambah Kamera"),
    ("21_keluarga_ringkasan", "21._keluarga_ringkasan_rumah/screen.png", "screen_21_keluarga_ringkasan_light_360.png", "Layar 21: Ringkasan Keluarga"),
    ("22_detail_kejadian", "22._detail_kejadian_keluarga_rumah/screen.png", "screen_22_detail_kejadian_light_360.png", "Layar 22: Detail Kejadian Keluarga"),
    ("23_lainnya", "23._lainnya_rumah/screen.png", "screen_23_lainnya_light_360.png", "Layar 23: Tab Lainnya"),
    ("24_notifikasi", "24._notifikasi_rumah/screen.png", "screen_24_notifikasi_light_360.png", "Layar 24: Notifikasi"),
    ("25_pengaturan", "25._pengaturan_sistem_rumah/screen.png", "screen_25_pengaturan_light_360.png", "Layar 25: Pengaturan Sistem"),
    ("26_kelola_anggota", "26._kelola_anggota_rumah/screen.png", "screen_26_kelola_anggota_light_360.png", "Layar 26: Kelola Anggota"),
    ("27_shell_bottom_nav", "3._beranda_rumah/screen.png", "screen_27_shell_bottom_nav_light_360.png", "Layar 27: Shell & Bottom Nav"),
]

def make_comparison(pair_id, stitch_rel, golden_rel, title):
    stitch_path = STITCH_DIR / stitch_rel
    golden_path = GOLDEN_DIR / golden_rel

    if not stitch_path.exists():
        print(f"[LEWAT] Berkas Stitch tidak ditemukan: {stitch_path}")
        return False
    if not golden_path.exists():
        print(f"[LEWAT] Berkas Golden tidak ditemukan: {golden_path}")
        return False

    img_stitch = Image.open(stitch_path).convert("RGB")
    img_golden = Image.open(golden_path).convert("RGB")

    # Tentukan dimensi kanvas
    # Lebar target per gambar: 360 px
    w_target = 360
    
    # Skalakan stitch jika lebarnya berbeda dari 360
    if img_stitch.width != w_target:
        new_h = int(img_stitch.height * (w_target / img_stitch.width))
        img_stitch = img_stitch.resize((w_target, new_h), Image.Resampling.LANCZOS)

    # Skalakan golden jika lebarnya berbeda dari 360
    if img_golden.width != w_target:
        new_h = int(img_golden.height * (w_target / img_golden.width))
        img_golden = img_golden.resize((w_target, new_h), Image.Resampling.LANCZOS)

    content_h = max(img_stitch.height, img_golden.height)
    
    # Header bar tinggi 50 px, padding samping 16 px, padding tengah 24 px
    header_h = 50
    padding_x = 20
    gap = 24
    total_w = (padding_x * 2) + (w_target * 2) + gap
    total_h = header_h + content_h + 24

    # Warna kanvas: background netral Quiet Domesticity #E8E5DF
    canvas = Image.new("RGB", (total_w, total_h), (232, 229, 223))
    draw = ImageDraw.Draw(canvas)

    # Header title
    try:
        font_title = ImageFont.truetype(str(ROOT_DIR / "app" / "assets" / "fonts" / "PublicSans-SemiBold.ttf"), 16)
        font_sub = ImageFont.truetype(str(ROOT_DIR / "app" / "assets" / "fonts" / "PublicSans-Regular.ttf"), 13)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Teks label kiri & kanan
    draw.text((padding_x + 10, 16), f"Google Stitch: {title}", fill=(47, 56, 50), font=font_title)
    draw.text((padding_x + w_target + gap + 10, 16), f"Flutter (Implementasi Riil)", fill=(47, 107, 91), font=font_title)

    # Tempel gambar Stitch di kiri
    canvas.paste(img_stitch, (padding_x, header_h))

    # Tempel gambar Golden di kanan
    canvas.paste(img_golden, (padding_x + w_target + gap, header_h))

    # Simpan hasil perbandingan
    out_file = COMPARE_DIR / f"compare_{pair_id}.png"
    canvas.save(out_file, quality=95)
    print(f"[BERHASIL] Lembar perbandingan dibuat: {out_file.name}")
    return True

def main():
    COMPARE_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for p in PAIRS:
        if make_comparison(p[0], p[1], p[2], p[3]):
            count += 1
    print(f"\nTotal lembar perbandingan selesai dibuat: {count} dari {len(PAIRS)}")

if __name__ == "__main__":
    main()
