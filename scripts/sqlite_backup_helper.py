#!/usr/bin/env python3
"""
Helper SQLite Online Backup API — Tahap 7.
Melakukan snapshot database SQLite secara konsisten dan atomik
meskipun server sedang aktif dalam mode WAL (Write-Ahead Logging).
"""

import argparse
import hashlib
import sqlite3
import sys
from pathlib import Path


def backup_sqlite(source_path: Path, target_path: Path) -> bool:
    if not source_path.exists():
        print(f"[!] Database sumber tidak ditemukan: {source_path}", file=sys.stderr)
        return False

    target_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[*] Melakukan SQLite Online Backup dari {source_path} ke {target_path}...")
    try:
        src_conn = sqlite3.connect(str(source_path))
        dst_conn = sqlite3.connect(str(target_path))

        # Menggunakan SQLite Online Backup API
        src_conn.backup(dst_conn, pages=100)

        dst_conn.close()
        src_conn.close()

        # Verifikasi integritas database hasil backup
        check_conn = sqlite3.connect(str(target_path))
        cursor = check_conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        res = cursor.fetchone()
        check_conn.close()

        if res and res[0] == "ok":
            print(f"[+] Backup SQLite berhasil dan terverifikasi 'ok'. Ukuran: {target_path.stat().st_size} bytes.")
            return True
        else:
            print(f"[!] Peringatan integritas database backup: {res}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"[!] Gagal melakukan online backup: {e}", file=sys.stderr)
        return False


def verify_sqlite_integrity(db_path: Path) -> bool:
    if not db_path.exists():
        print(f"[!] Database tidak ditemukan: {db_path}", file=sys.stderr)
        return False
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        res = cursor.fetchone()
        conn.close()
        is_ok = bool(res and res[0] == "ok")
        print(f"[*] Integritas {db_path.name}: {'LULUS (ok)' if is_ok else f'GAGAL ({res})'}")
        return is_ok
    except Exception as e:
        print(f"[!] Gagal memeriksa integritas: {e}", file=sys.stderr)
        return False


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="SQLite Online Backup Helper")
    parser.add_argument("--source", required=True, help="Path ke database sumber")
    parser.add_argument("--target", required=True, help="Path ke file database target backup")
    parser.add_argument("--verify-only", action="store_true", help="Hanya periksa integritas target")

    args = parser.parse_args()
    src = Path(args.source)
    dst = Path(args.target)

    if args.verify_only:
        ok = verify_sqlite_integrity(dst)
        sys.exit(0 if ok else 1)

    ok = backup_sqlite(src, dst)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
