#!/usr/bin/env python3
"""
Skrip Rotasi Kunci Enkripsi Media (AES-256-GCM) — Tahap 7.
Mendekripsi seluruh berkas rekaman (.enc) lama dengan kunci lama dan
mengenalisasi ulang menggunakan kunci baru secara aman tanpa merusak data.
"""

import argparse
import hashlib
import os
import re
import secrets
import shutil
import sqlite3
import sys
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def parse_key(raw_key: str) -> bytes:
    """Konversi string kunci (hex 64-char atau string UTF-8) menjadi 32 bytes."""
    raw_key = raw_key.strip()
    if len(raw_key) == 64:
        try:
            return bytes.fromhex(raw_key)
        except ValueError:
            pass
    return hashlib.sha256(raw_key.encode("utf-8")).digest()


def read_current_env_key(env_path: Path) -> str:
    """Baca MEDIA_ENCRYPTION_KEY saat ini dari file .env."""
    if not env_path.exists():
        raise FileNotFoundError(f"File konfigurasi {env_path} tidak ditemukan.")

    content = env_path.read_text(encoding="utf-8")
    match = re.search(r"^\s*MEDIA_ENCRYPTION_KEY\s*=\s*(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def update_env_key(env_path: Path, new_key_hex: str):
    """Perbarui MEDIA_ENCRYPTION_KEY di dalam file .env."""
    content = env_path.read_text(encoding="utf-8")
    if re.search(r"^\s*MEDIA_ENCRYPTION_KEY\s*=", content, re.MULTILINE):
        new_content = re.sub(
            r"^\s*MEDIA_ENCRYPTION_KEY\s*=.*$",
            f"MEDIA_ENCRYPTION_KEY={new_key_hex}",
            content,
            flags=re.MULTILINE,
        )
    else:
        new_content = content + f"\nMEDIA_ENCRYPTION_KEY={new_key_hex}\n"

    # Simpan backup sebelum menulis
    shutil.copy2(env_path, env_path.with_suffix(".env.bak"))
    env_path.write_text(new_content, encoding="utf-8")


def rotate_media_keys(
    db_path: Path,
    env_path: Path,
    new_key_hex: str,
    dry_run: bool = False,
) -> dict:
    """Melakukan rotasi kunci pada rekaman motion_clips dan memperbarui .env."""
    print("=" * 65)
    print("  [NEXA HOME — ROTASI KUNCI ENKRIPSI DATA DIAM (AES-256-GCM)]")
    print("=" * 65)

    old_raw_key = read_current_env_key(env_path)
    old_key_bytes = parse_key(old_raw_key)
    new_key_bytes = parse_key(new_key_hex)

    print(f"[*] Path Database : {db_path}")
    print(f"[*] Path .env     : {env_path}")
    print(f"[*] Kunci Lama    : {old_raw_key[:8]}...{old_raw_key[-8:]}")
    print(f"[*] Kunci Baru    : {new_key_hex[:8]}...{new_key_hex[-8:]}")
    print(f"[*] Mode Dry-Run  : {'YA (Simulasi Saja)' if dry_run else 'TIDAK (Terapkan Perubahan)'}\n")

    if not db_path.exists():
        print(f"[-] Database {db_path} belum dibuat. Hanya memperbarui file .env.")
        if not dry_run:
            update_env_key(env_path, new_key_hex)
        return {"total": 0, "success": 0, "failed": 0, "env_updated": not dry_run}

    old_aes = AESGCM(old_key_bytes)
    new_aes = AESGCM(new_key_bytes)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Periksa apakah tabel motion_clips ada
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='motion_clips'")
    if not cursor.fetchone():
        print("[!] Tabel 'motion_clips' belum ada di database.")
        conn.close()
        if not dry_run:
            update_env_key(env_path, new_key_hex)
        return {"total": 0, "success": 0, "failed": 0, "env_updated": not dry_run}

    cursor.execute("SELECT id, camera_id, file_path, nonce, tag FROM motion_clips")
    rows = cursor.fetchall()

    total_clips = len(rows)
    success_count = 0
    failed_count = 0

    print(f"[*] Menemukan {total_clips} klip rekaman terdaftar di database.")

    updates = []
    for clip_id, camera_id, file_path_str, old_nonce_hex, tag in rows:
        clip_path = Path(file_path_str)
        if not clip_path.is_absolute():
            clip_path = db_path.parent.parent / clip_path

        if not clip_path.exists():
            print(f"  [-] Lewati clip {clip_id}: berkas tidak ada di disk ({clip_path})")
            continue

        try:
            old_ciphertext = clip_path.read_bytes()
            old_nonce = bytes.fromhex(old_nonce_hex)
            aad = camera_id.encode("utf-8") if camera_id else None

            # 1. Dekripsi data menggunakan kunci lama
            plaintext = old_aes.decrypt(old_nonce, old_ciphertext, aad)

            # 2. Enkripsi ulang menggunakan kunci baru + nonce baru
            new_nonce = os.urandom(12)
            new_ciphertext = new_aes.encrypt(new_nonce, plaintext, aad)

            # 3. Verifikasi ulang sebelum menimpa
            verify_plaintext = new_aes.decrypt(new_nonce, new_ciphertext, aad)
            assert verify_plaintext == plaintext, "Verifikasi integritas gagal"

            if not dry_run:
                # Tulis kembali ciphertext baru ke disk
                clip_path.write_bytes(new_ciphertext)
                updates.append((new_nonce.hex(), clip_id))

            success_count += 1
            print(f"  [+] Klip {clip_id} berhasil dienkripsi ulang dengan kunci baru.")
        except Exception as e:
            failed_count += 1
            print(f"  [!] Gagal memproses klip {clip_id}: {e}")

    if not dry_run:
        # Perbarui nonce di database
        for new_nonce_str, clip_id in updates:
            cursor.execute("UPDATE motion_clips SET nonce=? WHERE id=?", (new_nonce_str, clip_id))
        conn.commit()
        # Perbarui kunci di .env
        update_env_key(env_path, new_key_hex)
        print("\n[+] Berhasil memperbarui MEDIA_ENCRYPTION_KEY di .env!")

    conn.close()

    print("\n" + "=" * 65)
    print(f"  RINGKASAN ROTASI KUNCI:")
    print(f"  - Total Klip    : {total_clips}")
    print(f"  - Sukses Rotasi : {success_count}")
    print(f"  - Gagal         : {failed_count}")
    print(f"  - Status .env   : {'Diperbarui' if not dry_run else 'Tidak Berubah (Simulasi)'}")
    print("=" * 65 + "\n")

    return {
        "total": total_clips,
        "success": success_count,
        "failed": failed_count,
        "env_updated": not dry_run,
    }


def main():
    parser = argparse.ArgumentParser(description="Alat Rotasi Kunci Enkripsi Media Nexa Home")
    parser.add_argument("--new-key", help="Kunci 64-karakter hex baru (opsional jika --generate)")
    parser.add_argument("--generate-key", action="store_true", help="Otomatis buat kunci 256-bit baru secara acak")
    parser.add_argument("--dry-run", action="store_true", help="Jalankan simulasi tanpa mengubah data disk/.env")
    parser.add_argument("--db-path", default="server/data/rumah.db", help="Path ke database SQLite")
    parser.add_argument("--env-path", default=".env", help="Path ke file .env")

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    db_path = project_root / args.db_path
    env_path = project_root / args.env_path

    if args.generate_key:
        new_key = secrets.token_hex(32)
    elif args.new_key:
        new_key = args.new_key.strip()
    else:
        print("[!] Tentukan --new-key <hex> atau gunakan flag --generate-key")
        sys.exit(1)

    rotate_media_keys(db_path=db_path, env_path=env_path, new_key_hex=new_key, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
