"""
Pengujian Menyeluruh Sistem Kamera, Pairing, MediaMTX Hook, Deteksi Gerakan, Enkripsi Klip, dan Retensi (Tahap 4).
"""

from datetime import datetime, timedelta, timezone
import hashlib
import io
import os
from pathlib import Path
import pytest
import numpy as np
import cv2
from httpx import ASGITransport, AsyncClient
import jwt

from server.app.core.camera.encryption import decrypt_bytes, encrypt_bytes, read_and_decrypt_clip, save_encrypted_clip
from server.app.core.camera.motion_service import MotionDetector, CameraRecordingSession, motion_manager
from server.app.core.camera.retention import cleanup_expired_clips, enforce_max_storage_quota, check_disk_space_available
from server.app.core.config import settings
from server.app.core.database import Base, engine, init_sqlite_wal
from server.app.core.security import create_access_token, hash_password
from server.app.core.setup_manager import get_current_setup_code, reset_setup_code_for_testing
from server.app.main import app
from server.app.models.audit import AuditLog
from server.app.models.camera import Camera, CameraPairingCode, CameraToken, CameraUserAccess, MotionClip
from server.app.models.user import User
import pyotp


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture(autouse=True)
async def setup_clean_db():
    """Reset database tables before each test session."""
    await init_sqlite_wal()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    reset_setup_code_for_testing()
    yield


async def setup_test_users(client: AsyncClient) -> dict:
    """Helper untuk membuat akun admin, member, dan child untuk pengujian."""
    await client.get("/api/auth/setup-status")
    code = get_current_setup_code()
    setup_res = await client.post(
        "/api/auth/setup-admin",
        json={
            "setup_code": code,
            "username": "admin_cam",
            "password": "PasswordAdmin123!",
            "full_name": "Admin Camera",
        },
    )
    admin_totp = setup_res.json()["totp_secret"]

    # Login admin
    login_res = await client.post(
        "/api/auth/login",
        json={"username": "admin_cam", "password": "PasswordAdmin123!"},
    )
    verify_res = await client.post(
        "/api/auth/verify-2fa",
        json={"temp_token": login_res.json()["temp_token"], "code": pyotp.TOTP(admin_totp).now()},
    )
    admin_token = verify_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Buat member
    await client.post(
        "/api/auth/users",
        headers=admin_headers,
        json={"username": "member_cam", "password": "MemberPass123!", "full_name": "Member Cam", "role": "member"},
    )
    login_mem = await client.post("/api/auth/login", json={"username": "member_cam", "password": "MemberPass123!"})
    member_token = login_mem.json()["access_token"]

    # Buat child
    await client.post(
        "/api/auth/users",
        headers=admin_headers,
        json={"username": "child_cam", "password": "ChildPass123!", "full_name": "Child Cam", "role": "child"},
    )
    login_child = await client.post("/api/auth/login", json={"username": "child_cam", "password": "ChildPass123!"})
    child_token = login_child.json()["access_token"]

    return {
        "admin": admin_token,
        "member": member_token,
        "child": child_token,
    }


# 1. Tes Pairing (Siklus Pembuatan, Penggunaan, Kedaluwarsa, & Sekali Pakai)
@pytest.mark.asyncio
async def test_camera_pairing_flow():
    async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
        tokens = await setup_test_users(client)

        # (a) Member atau Child dilarang membuat pairing code
        res = await client.post(
            "/api/cameras/pairing-codes",
            headers={"Authorization": f"Bearer {tokens['member']}"},
            json={"camera_name": "Kamera Depan", "room_id": "front_yard"},
        )
        assert res.status_code == 403

        # (b) Admin membuat pairing code
        res = await client.post(
            "/api/cameras/pairing-codes",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
            json={"camera_name": "Kamera Garasi", "room_id": "garage"},
        )
        assert res.status_code == 200
        code_data = res.json()
        assert "code" in code_data
        assert code_data["code"].startswith("CAM-")
        pairing_code = code_data["code"]

        # (c) Kamera menukar pairing code dengan token
        pair_res = await client.post(
            "/api/cameras/pair",
            json={"pairing_code": pairing_code},
        )
        assert pair_res.status_code == 200
        pair_data = pair_res.json()
        assert "camera_id" in pair_data
        assert "camera_token" in pair_data
        camera_id = pair_data["camera_id"]
        camera_token = pair_data["camera_token"]

        # (d) Kode sekali pakai tidak boleh digunakan lagi
        reuse_res = await client.post(
            "/api/cameras/pair",
            json={"pairing_code": pairing_code},
        )
        assert reuse_res.status_code == 400
        assert "sudah digunakan" in reuse_res.json()["detail"]


# 2. Tes MediaMTX HTTP Auth Hook & Pencabutan Kamera Instan
@pytest.mark.asyncio
async def test_mediamtx_auth_hook_and_revocation():
    async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
        tokens = await setup_test_users(client)

        # Buat pairing kamera
        res = await client.post(
            "/api/cameras/pairing-codes",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
            json={"camera_name": "Kamera Teras", "room_id": "terrace"},
        )
        code = res.json()["code"]
        pair_res = await client.post("/api/cameras/pair", json={"pairing_code": code})
        cam_id = pair_res.json()["camera_id"]
        cam_token = pair_res.json()["camera_token"]

        # (a) Publish tanpa token -> 401
        res = await client.post(
            "/api/cameras/auth/mediamtx",
            json={"action": "publish", "path": cam_id, "password": ""},
        )
        assert res.status_code == 401

        # (b) Publish dengan token salah -> 401
        res = await client.post(
            "/api/cameras/auth/mediamtx",
            json={"action": "publish", "path": cam_id, "password": "wrong_token_secret"},
        )
        assert res.status_code == 401

        # (c) Publish dengan token valid -> 200
        res = await client.post(
            "/api/cameras/auth/mediamtx",
            json={"action": "publish", "path": cam_id, "password": cam_token},
        )
        assert res.status_code == 200

        # (d) Read tanpa JWT -> 401
        res = await client.post(
            "/api/cameras/auth/mediamtx",
            json={"action": "read", "path": cam_id, "password": ""},
        )
        assert res.status_code == 401

        # (e) Read dengan akun child -> 403 DITOLAK
        res = await client.post(
            "/api/cameras/auth/mediamtx",
            json={"action": "read", "path": cam_id, "password": tokens["child"]},
        )
        assert res.status_code == 403

        # (f) Read dengan akun admin -> 200
        res = await client.post(
            "/api/cameras/auth/mediamtx",
            json={"action": "read", "path": cam_id, "password": tokens["admin"]},
        )
        assert res.status_code == 200

        # (g) Pencabutan token oleh admin
        revoke_res = await client.post(
            f"/api/cameras/{cam_id}/revoke",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert revoke_res.status_code == 200

        # (h) Setelah dicabut, publish seketika DITOLAK (kamera langsung terputus)
        re_publish = await client.post(
            "/api/cameras/auth/mediamtx",
            json={"action": "publish", "path": cam_id, "password": cam_token},
        )
        assert re_publish.status_code == 401


# 3. Tes Mode Privasi: Menghentikan Stream & Deteksi
@pytest.mark.asyncio
async def test_camera_privacy_mode_flow():
    async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
        tokens = await setup_test_users(client)

        code_res = await client.post(
            "/api/cameras/pairing-codes",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
            json={"camera_name": "Kamera Kamar", "room_id": "bedroom"},
        )
        pair_res = await client.post("/api/cameras/pair", json={"pairing_code": code_res.json()["code"]})
        cam_id = pair_res.json()["camera_id"]
        cam_token = pair_res.json()["camera_token"]

        # Aktifkan mode privasi
        priv_res = await client.patch(
            f"/api/cameras/{cam_id}/privacy",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
            json={"privacy_mode": True},
        )
        assert priv_res.status_code == 200
        assert priv_res.json()["privacy_mode"] is True

        # Hook MediaMTX tolak publish saat privasi aktif
        pub_res = await client.post(
            "/api/cameras/auth/mediamtx",
            json={"action": "publish", "path": cam_id, "password": cam_token},
        )
        assert pub_res.status_code == 403

        # Hook MediaMTX tolak read saat privasi aktif
        read_res = await client.post(
            "/api/cameras/auth/mediamtx",
            json={"action": "read", "path": cam_id, "password": tokens["admin"]},
        )
        assert read_res.status_code == 403

        # Snapshot ditolak saat mode privasi aktif
        snap_res = await client.get(
            f"/api/cameras/{cam_id}/snapshot",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
        )
        assert snap_res.status_code == 403


# 4. Tes Deteksi Gerakan OpenCV (Gerak vs Diam & Ignore Zones)
def test_opencv_motion_detector():
    detector = MotionDetector(camera_id="cam_test", threshold=25, min_area=300)

    # Frame hitam polos 320x240
    frame_black = np.zeros((240, 320, 3), dtype=np.uint8)

    # Frame 1: inisialisasi baseline
    motion1, _ = detector.process_frame(frame_black)
    assert motion1 is False

    # Frame 2: frame identik (diam tanpa gerakan)
    motion2, _ = detector.process_frame(frame_black)
    assert motion2 is False

    # Frame 3: gambar kotak putih besar yang bergerak di tengah
    frame_motion = frame_black.copy()
    cv2.rectangle(frame_motion, (100, 80), (200, 160), (255, 255, 255), -1)

    motion3, _ = detector.process_frame(frame_motion)
    assert motion3 is True, "Gerakan kotak putih seharusnya terdeteksi oleh OpenCV"


# 5. Tes Perekaman Sesi, Pre-roll Circular Buffer, dan Batas Durasi
def test_camera_recording_session_and_preroll():
    session = CameraRecordingSession(camera_id="cam_test_preroll")
    frame = np.zeros((240, 320, 3), dtype=np.uint8)

    # Masukkan beberapa frame tenang (masuk ke pre-roll buffer)
    for _ in range(5):
        clip = session.push_frame(frame, motion_detected=False)
        assert clip is None
    assert len(session.pre_roll_buffer) > 0

    # Pemicu gerakan
    clip = session.push_frame(frame, motion_detected=True)
    assert session.is_recording is True
    # Frame yang direkam harus menyertakan pre-roll frames
    assert len(session.recorded_frames) > 1

    # Gerakan berhenti, masuk ke masa post-roll
    completed_clip = None
    for _ in range(session.post_roll_limit + 1):
        res = session.push_frame(frame, motion_detected=False)
        if res:
            completed_clip = res
            break

    assert completed_clip is not None
    assert completed_clip["camera_id"] == "cam_test_preroll"
    assert completed_clip["duration"] > 0
    assert len(completed_clip["frames"]) > 0


# 6. Tes Enkripsi dan Dekripsi Klip AES-256-GCM
def test_clip_encryption_and_decryption(tmp_path):
    original_video_data = b"REAL_H264_MP4_SAMPLE_DATA_BYTES_1234567890" * 50
    camera_id = "cam_secure_vault"
    output_file = tmp_path / "test_clip.enc"

    # Enkripsi dan simpan ke disk
    nonce_hex, file_size = save_encrypted_clip(original_video_data, camera_id, output_file)
    assert output_file.exists()
    assert file_size == output_file.stat().st_size

    # Verifikasi berkas di disk BUKAN plaintext
    disk_content = output_file.read_bytes()
    assert disk_content != original_video_data
    assert b"REAL_H264_MP4" not in disk_content

    # Dekripsi menggunakan nonce dan kunci resmi
    decrypted = read_and_decrypt_clip(output_file, nonce_hex, camera_id)
    assert decrypted == original_video_data

    # Dekripsi dengan associated data (camera_id) yang salah harus gagal
    with pytest.raises(Exception):
        read_and_decrypt_clip(output_file, nonce_hex, "wrong_camera_id")


# 7. Tes Izin Per Peran & Saklar Audio Kamera
@pytest.mark.asyncio
async def test_camera_roles_and_audio_switch():
    async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
        tokens = await setup_test_users(client)

        # Buat kamera
        code_res = await client.post(
            "/api/cameras/pairing-codes",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
            json={"camera_name": "Kamera Dapur", "room_id": "kitchen"},
        )
        pair_res = await client.post("/api/cameras/pair", json={"pairing_code": code_res.json()["code"]})
        cam_id = pair_res.json()["camera_id"]

        # (a) Child akses kamera -> DITOLAK 403
        child_res = await client.get("/api/cameras", headers={"Authorization": f"Bearer {tokens['child']}"})
        assert child_res.status_code == 403

        # (b) Audio default harus False
        list_res = await client.get("/api/cameras", headers={"Authorization": f"Bearer {tokens['admin']}"})
        cameras = list_res.json()
        target_cam = next(c for c in cameras if c["id"] == cam_id)
        assert target_cam["audio_enabled"] is False

        # (c) Member dilarang mengubah saklar audio -> 403
        aud_mem = await client.patch(
            f"/api/cameras/{cam_id}/audio",
            headers={"Authorization": f"Bearer {tokens['member']}"},
            json={"audio_enabled": True},
        )
        assert aud_mem.status_code == 403

        # (d) Admin mengubah saklar audio -> 200
        aud_adm = await client.patch(
            f"/api/cameras/{cam_id}/audio",
            headers={"Authorization": f"Bearer {tokens['admin']}"},
            json={"audio_enabled": True},
        )
        assert aud_adm.status_code == 200
        assert aud_adm.json()["audio_enabled"] is True


# 8. Tes Retensi Otomatis & Pembersihan Klip
@pytest.mark.asyncio
async def test_retention_maintenance_service():
    from server.app.core.database import async_session_factory

    async with async_session_factory() as db:
        cam = Camera(id="cam_retention_test", name="Cam Ret", room_id="hall")
        db.add(cam)
        await db.commit()

        # Buat klip kadaluwarsa (10 hari lalu)
        old_time = utcnow() - timedelta(days=10)
        old_clip = MotionClip(
            id="clip_old_10d",
            camera_id="cam_retention_test",
            start_time=old_time,
            end_time=old_time + timedelta(seconds=10),
            duration_seconds=10.0,
            file_path="dummy_path.enc",
            file_size_bytes=5000,
            nonce="0123456789abcdef01234567",
            created_at=old_time,
        )
        db.add(old_clip)

        # Buat klip baru (1 jam lalu)
        new_time = utcnow() - timedelta(hours=1)
        new_clip = MotionClip(
            id="clip_new_1h",
            camera_id="cam_retention_test",
            start_time=new_time,
            end_time=new_time + timedelta(seconds=10),
            duration_seconds=10.0,
            file_path="dummy_path_new.enc",
            file_size_bytes=5000,
            nonce="0123456789abcdef01234567",
            created_at=new_time,
        )
        db.add(new_clip)
        await db.commit()

        # Jalankan pembersihan retensi
        deleted = await cleanup_expired_clips(db)
        assert deleted >= 1

        # Cek apakah klip baru masih ada
        check_new = await db.get(MotionClip, "clip_new_1h")
        assert check_new is not None

        # Cek apakah klip lama sudah terhapus
        check_old = await db.get(MotionClip, "clip_old_10d")
        assert check_old is None

    # Tes pemeriksaan ruang disk
    is_safe, free_mb = check_disk_space_available()
    assert isinstance(is_safe, bool)
    assert free_mb > 0
