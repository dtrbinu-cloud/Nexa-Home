#!/usr/bin/env python3
"""
Simulasi Pengujian Otomatis Backup & Restore — Tahap 7.
Alur Pengujian:
1. Seed Data: Buat database terisolasi dan klip terenkripsi AES-256-GCM.
2. Backup: Buat snapshot konsisten via SQLite Online Backup API & kompresi ZIP.
3. Mutasi / Kerusakan Bencana: Hapus data database dan hapus klip dari disk.
4. Restore: Pulihkan seluruh data dari arsip ZIP cadangan.
5. Verifikasi: Periksa integritas PRAGMA, pastikan jumlah entitas dan hash berkas kembali 100% utuh.
"""

import hashlib
import os
import shutil
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from server.app.core.camera.encryption import encrypt_bytes, decrypt_bytes
from scripts.sqlite_backup_helper import backup_sqlite, verify_sqlite_integrity


def run_simulation() -> bool:
    print("=" * 70)
    print("  SIMULASI PENGUJIAN OTOMATIS: BACKUP -> DELETION -> RESTORE -> VERIFY")
    print("=" * 70)

    temp_dir = Path(tempfile.mkdtemp(prefix="nexa_sim_test_"))
    try:
        sim_db_path = temp_dir / "sim_rumah.db"
        sim_clips_dir = temp_dir / "clips"
        sim_backup_dir = temp_dir / "backups"
        sim_clips_dir.mkdir(parents=True, exist_ok=True)
        sim_backup_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n[1/5] SEEDING DATA SIMULASI...")
        conn = sqlite3.connect(str(sim_db_path))
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode = WAL;")
        cur.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                email TEXT,
                role TEXT
            );
        """)
        cur.execute("""
            CREATE TABLE devices (
                id TEXT PRIMARY KEY,
                name TEXT,
                type TEXT
            );
        """)
        cur.execute("""
            CREATE TABLE motion_clips (
                id TEXT PRIMARY KEY,
                camera_id TEXT,
                file_path TEXT,
                nonce TEXT
            );
        """)

        # Insert 3 users
        test_users = [
            (1, "admin_rumah", "admin@aujasena.my.id", "admin"),
            (2, "member_budi", "budi@aujasena.my.id", "member"),
            (3, "child_dina", "dina@aujasena.my.id", "child"),
        ]
        cur.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", test_users)

        # Insert 2 devices
        test_devices = [
            ("lamp_living_room", "Lampu Ruang Tamu", "relay"),
            ("sensor_kitchen", "Sensor Gas Dapur", "sensor"),
        ]
        cur.executemany("INSERT INTO devices VALUES (?, ?, ?)", test_devices)

        # Buat berkas video rekaman klip terenkripsi (AES-256-GCM)
        sample_video_payload = b"NEXA_HOME_SIMULATED_VIDEO_STREAM_BYTES_SAMPLE_DATA_1234567890" * 50
        ciphertext, nonce_hex = encrypt_bytes(sample_video_payload, associated_data="cam_front_yard")
        clip_file = sim_clips_dir / "clip_sim_001.enc"
        clip_file.write_bytes(ciphertext)
        original_clip_sha256 = hashlib.sha256(ciphertext).hexdigest()

        cur.execute(
            "INSERT INTO motion_clips VALUES (?, ?, ?, ?)",
            ("clip_001", "cam_front_yard", str(clip_file), nonce_hex),
        )
        conn.commit()
        conn.close()

        print(f"  [+] Terbuat 3 Pengguna, 2 Perangkat, dan 1 Klip Terenkripsi (SHA256: {original_clip_sha256[:16]}...)")

        # 2. PROSES BACKUP
        print(f"\n[2/5] MENJALANKAN ONLINE BACKUP SECARA ATOMIK...")
        staged_db = temp_dir / "staged_rumah.db"
        ok_backup = backup_sqlite(sim_db_path, staged_db)
        assert ok_backup, "Online backup SQLite gagal!"

        backup_zip = sim_backup_dir / "sim_backup.zip"
        with zipfile.ZipFile(backup_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(staged_db, arcname="rumah.db")
            zf.write(clip_file, arcname=f"clips/{clip_file.name}")

        print(f"  [+] Arsip cadangan dibuat: {backup_zip.name} ({backup_zip.stat().st_size} bytes)")

        # 3. SIMULASI BENCANA / HAPUS DATA
        print(f"\n[3/5] SIMULASI BENCANA: MERUSAK DATABASE & MENGHAPUS DATA...")
        conn_corrupt = sqlite3.connect(str(sim_db_path))
        cur_c = conn_corrupt.cursor()
        cur_c.execute("DELETE FROM users;")
        cur_c.execute("DELETE FROM devices;")
        cur_c.execute("DELETE FROM motion_clips;")
        conn_corrupt.commit()
        conn_corrupt.close()

        # Hapus berkas klip dari disk
        clip_file.unlink()

        # Verifikasi data benar-benar hilang sebelum dipulihkan
        conn_check = sqlite3.connect(str(sim_db_path))
        c_users = conn_check.execute("SELECT count(*) FROM users").fetchone()[0]
        c_devs = conn_check.execute("SELECT count(*) FROM devices").fetchone()[0]
        conn_check.close()

        assert c_users == 0 and c_devs == 0, "Data belum terhapus untuk simulasi!"
        assert not clip_file.exists(), "Berkas klip belum terhapus untuk simulasi!"
        print("  [-] Data database dikosongkan (users=0, devices=0) dan klip rekaman dihapus dari disk.")

        # 4. PROSES RESTORE
        print(f"\n[4/5] MEMULIHKAN DATA DARI ARSIP CADANGAN...")
        extract_dir = temp_dir / "extracted"
        with zipfile.ZipFile(backup_zip, "r") as zf:
            zf.extractall(extract_dir)

        # Verifikasi integritas database hasil ekstrak
        restored_db_src = extract_dir / "rumah.db"
        assert verify_sqlite_integrity(restored_db_src), "Database yang diekstrak tidak valid!"

        # Pulihkan ke lokasi utama
        shutil.copy2(restored_db_src, sim_db_path)
        restored_clip_src = extract_dir / "clips" / clip_file.name
        shutil.copy2(restored_clip_src, clip_file)

        print("  [+] Database dan berkas rekaman berhasil disalin kembali ke direktori aktif.")

        # 5. VERIFIKASI KEUTUHAN DATA
        print(f"\n[5/5] VERIFIKASI DATA KEMBALI UTUH...")
        # Periksa integritas PRAGMA
        assert verify_sqlite_integrity(sim_db_path), "Integritas database setelah restore gagal!"

        conn_verif = sqlite3.connect(str(sim_db_path))
        verif_users = conn_verif.execute("SELECT id, username, email, role FROM users ORDER BY id").fetchall()
        verif_devs = conn_verif.execute("SELECT id, name, type FROM devices ORDER BY id").fetchall()
        verif_clips = conn_verif.execute("SELECT id, camera_id, nonce FROM motion_clips").fetchall()
        conn_verif.close()

        assert verif_users == test_users, f"Data pengguna tidak cocok! Ditemukan: {verif_users}"
        assert verif_devs == test_devices, f"Data perangkat tidak cocok! Ditemukan: {verif_devs}"
        assert len(verif_clips) == 1, "Data klip di database tidak ditemukan!"

        # Verifikasi hash berkas terenkripsi
        restored_clip_bytes = clip_file.read_bytes()
        restored_clip_sha256 = hashlib.sha256(restored_clip_bytes).hexdigest()
        assert restored_clip_sha256 == original_clip_sha256, "Hash SHA256 klip berbeda setelah restore!"

        # Verifikasi bahwa video terenkripsi dapat didekripsi dengan sempurna
        decrypted_payload = decrypt_bytes(
            restored_clip_bytes,
            verif_clips[0][2],
            associated_data=verif_clips[0][1],
        )
        assert decrypted_payload == sample_video_payload, "Payload rekaman video hasil dekripsi tidak cocok!"

        print("\n" + "=" * 70)
        print("  [HASIL PENGUJIAN]: LULUS 100%!")
        print("  - Integritas Database : PRAGMA integrity_check = 'ok'")
        print(f"  - Tabel Users         : 3/3 record kembali utuh ({[u[1] for u in verif_users]})")
        print(f"  - Tabel Devices       : 2/2 record kembali utuh ({[d[0] for d in verif_devs]})")
        print(f"  - Klip Terenkripsi    : SHA-256 identik ({restored_clip_sha256[:16]}...)")
        print("  - Validasi AES-GCM    : Sukses didekripsi menjadi payload byte asli")
        print("=" * 70 + "\n")
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    success = run_simulation()
    sys.exit(0 if success else 1)
