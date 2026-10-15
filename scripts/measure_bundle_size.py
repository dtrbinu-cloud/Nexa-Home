#!/usr/bin/env python3
"""
scripts/measure_bundle_size.py — Mengukur ukuran bundle web produksi (web/dist)
Menghitung ukuran asli dan ukuran terkompresi gzip untuk file statis.
"""
import gzip
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "web" / "dist"

def main():
    if not DIST_DIR.exists():
        print(f"Error: {DIST_DIR} tidak ditemukan. Jalankan 'npm run build' di folder web terlebih dahulu.")
        return

    print("=== Pengukuran Ukuran Bundle Produksi (web/dist) ===")
    total_raw = 0
    total_gzip = 0
    file_records = []

    for root, _, files in os.walk(DIST_DIR):
        for f in files:
            p = Path(root) / f
            rel = p.relative_to(DIST_DIR)
            raw_size = p.stat().st_size
            total_raw += raw_size

            # Hitung ukuran gzip
            with open(p, "rb") as fp:
                data = fp.read()
                gz_data = gzip.compress(data, compresslevel=9)
                gz_size = len(gz_data)
                total_gzip += gz_size

            file_records.append((str(rel), raw_size, gz_size))

    # Sort berdasarkan raw size descending
    file_records.sort(key=lambda x: x[1], reverse=True)

    print(f"{'File Path':<45} | {'Raw (KB)':<10} | {'Gzip (KB)':<10}")
    print("-" * 71)
    for path, raw, gz in file_records:
        print(f"{path:<45} | {raw / 1024:>9.2f} | {gz / 1024:>9.2f}")
    print("-" * 71)
    print(f"{'TOTAL':<45} | {total_raw / 1024:>9.2f} | {total_gzip / 1024:>9.2f}")

if __name__ == "__main__":
    main()
