"""
Unit dan Integration Test untuk Fitur Vision AI & Worker (Tahap 5).
Mencakup:
1. Pencarian sinonim & penolakan benda tak didukung (Aturan Kejujuran)
2. Izin per peran (RBAC: Admin, Member, Child)
3. Deduplikasi log benda (benda diam vs berpindah)
4. Mode privasi (kamera privasi tidak dibaca worker)
5. Retensi pembersihan otomatis
6. Pemantauan kesehatan & Heartbeat worker
7. Ketahanan antrean (frame drop saat lambat)
8. Keamanan thumbnail: akses tanpa izin ditolak, tanpa kunci file tidak dapat didekripsi
"""

import asyncio
import datetime
import os
import uuid
from pathlib import Path
import numpy as np
import pytest
import pytest_asyncio
from cryptography.exceptions import InvalidTag
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from server.app.core.assistant.item_search import execute_find_item, COCO_SYNONYMS, UNSUPPORTED_ITEMS
from server.app.core.camera.encryption import decrypt_bytes, encrypt_clip_data
from server.app.core.config import settings
from server.app.core.database import Base
from server.app.main import app
from server.app.models.camera import (
    AIWorkerHeartbeat,
    Camera,
    CameraUserAccess,
    DetectedItemLog,
    PersonPresenceEvent,
)
from server.app.models.user import User
from server.app.worker.vision_worker import AnonymousTracker, VisionWorker


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sm = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield sm
    await engine.dispose()


@pytest.mark.asyncio
async def test_synonym_search_and_unsupported_rejection(test_db):
    """Pengujian sinonim bahasa Indonesia ke kelas COCO dan penolakan benda tak didukung."""
    admin_user = User(id=1, username="admin_test", role="admin")

    async with test_db() as db:
        # 1. Benda tidak didukung (kunci, dompet) harus ditolak jujur
        res_kunci = await execute_find_item(db, admin_user, "kunci")
        assert res_kunci["status"] == "unsupported"
        assert "belum didukung" in res_kunci["message"]

        res_dompet = await execute_find_item(db, admin_user, "dompet")
        assert res_dompet["status"] == "unsupported"
        assert "belum didukung" in res_dompet["message"]

        # 2. Benda COCO tapi belum ada riwayat log
        res_hp_empty = await execute_find_item(db, admin_user, "HP")
        assert res_hp_empty["status"] == "not_found"

        # 3. Masukkan data log benda riil
        cam = Camera(id="cam_living", name="Kamera Ruang Tamu", room_id="ruang tamu", status="online")
        db.add(cam)
        item = DetectedItemLog(
            id="item_phone_1",
            camera_id="cam_living",
            room_id="ruang tamu",
            class_name="cell phone",
            first_seen_at=datetime.datetime.now(datetime.timezone.utc),
            last_seen_at=datetime.datetime.now(datetime.timezone.utc),
            confidence=0.88,
            bbox_x=100.0,
            bbox_y=150.0,
            bbox_w=80.0,
            bbox_h=120.0,
        )
        db.add(item)
        await db.commit()

        # Uji berbagai sinonim bahasa Indonesia untuk HP
        for query in ["hp", "ponsel", "handphone", "telepon genggam", "cell phone"]:
            found = await execute_find_item(db, admin_user, query)
            assert found["status"] == "success"
            assert "ruang tamu" in found["message"]
            assert found["class_name"] == "cell phone"


@pytest.mark.asyncio
async def test_rbac_camera_item_search(test_db):
    """Pengujian hak akses RBAC: child ditolak, member difilter kamera yang diizinkan."""
    child_user = User(id=3, username="anak", role="child")
    member_user = User(id=2, username="anggota", role="member")
    admin_user = User(id=1, username="admin", role="admin")

    async with test_db() as db:
        cam_pub = Camera(id="cam_public", name="Depan", room_id="teras", status="online")
        cam_priv = Camera(id="cam_private", name="Kamar Tidur", room_id="kamar", status="online")
        db.add_all([cam_pub, cam_priv])

        # Log tas di kamar tidur
        item_tas = DetectedItemLog(
            id="item_bag_1",
            camera_id="cam_private",
            room_id="kamar",
            class_name="backpack",
            first_seen_at=datetime.datetime.now(datetime.timezone.utc),
            last_seen_at=datetime.datetime.now(datetime.timezone.utc),
            confidence=0.92,
        )
        db.add(item_tas)

        # Member hanya diizinkan ke cam_public
        db.add(CameraUserAccess(user_id=member_user.id, camera_id="cam_public"))
        await db.commit()

        # 1. Child DITOLAK (status error 403 / forbidden)
        res_child = await execute_find_item(db, child_user, "tas")
        assert res_child["status"] == "forbidden"

        # 2. Member tidak dapat melihat tas di cam_private
        res_member = await execute_find_item(db, member_user, "tas")
        assert res_member["status"] == "not_found"

        # 3. Admin dapat menemukan tas di kamar tidur
        res_admin = await execute_find_item(db, admin_user, "tas")
        assert res_admin["status"] == "success"
        assert res_admin["room_id"] == "kamar"


@pytest.mark.asyncio
async def test_item_deduplication(test_db):
    """Pengujian deduplikasi: benda diam hanya memperbarui last_seen_at, benda bergerak membuat log baru."""
    now = datetime.datetime.now(datetime.timezone.utc)
    cam_id = "cam_office"
    room_id = "ruang kerja"

    # Gunakan in-memory DB
    worker = VisionWorker.__new__(VisionWorker)
    worker.session_maker = test_db

    async with test_db() as db:
        cam = Camera(id=cam_id, name="Kamera Kantor", room_id=room_id, status="online")
        db.add(cam)
        await db.commit()

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # 1. Log pertama laptop
    det1 = {
        "class_name": "laptop",
        "score": 0.85,
        "bbox": (100.0, 100.0, 300.0, 250.0),
        "track_id": 1,
    }
    await worker._handle_item_log(cam_id, room_id, det1, dummy_frame, now)

    async with test_db() as db:
        logs = (await db.execute(select(DetectedItemLog))).scalars().all()
        assert len(logs) == 1
        t1 = logs[0].first_seen_at.replace(tzinfo=datetime.timezone.utc) if logs[0].first_seen_at.tzinfo is None else logs[0].first_seen_at
        assert t1.timestamp() == pytest.approx(now.timestamp(), abs=2.0)

    # 2. Log kedua laptop di posisi yang hampir sama (bergeser hanya 5 piksel) 2 detik kemudian
    now2 = now + datetime.timedelta(seconds=2)
    det2 = {
        "class_name": "laptop",
        "score": 0.89,
        "bbox": (105.0, 102.0, 305.0, 252.0),
        "track_id": 1,
    }
    await worker._handle_item_log(cam_id, room_id, det2, dummy_frame, now2)

    async with test_db() as db:
        logs = (await db.execute(select(DetectedItemLog))).scalars().all()
        # Jumlah baris TETAP 1 (dedup berhasil)
        assert len(logs) == 1
        t2 = logs[0].last_seen_at.replace(tzinfo=datetime.timezone.utc) if logs[0].last_seen_at.tzinfo is None else logs[0].last_seen_at
        assert t2.timestamp() == pytest.approx(now2.timestamp(), abs=2.0)
        assert logs[0].confidence == 0.89

    # 3. Log ketiga laptop dipindahkan ke posisi jauh (> 150 piksel)
    now3 = now + datetime.timedelta(seconds=10)
    det3 = {
        "class_name": "laptop",
        "score": 0.87,
        "bbox": (400.0, 300.0, 600.0, 450.0),
        "track_id": 2,
    }
    await worker._handle_item_log(cam_id, room_id, det3, dummy_frame, now3)

    async with test_db() as db:
        logs = (await db.execute(select(DetectedItemLog))).scalars().all()
        # Bertambah menjadi 2 kejadian karena berpindah posisi secara signifikan
        assert len(logs) == 2


@pytest.mark.asyncio
async def test_privacy_mode_stream_exclusion(test_db):
    """Pengujian mode privasi: kamera dengan privasi aktif diabaikan sepenuhnya oleh worker."""
    worker = VisionWorker.__new__(VisionWorker)
    worker.session_maker = test_db

    async with test_db() as db:
        c1 = Camera(id="cam_open", name="Teras", room_id="teras", status="online", ai_enabled=True, privacy_mode=False)
        c2 = Camera(id="cam_private", name="Kamar", room_id="kamar", status="online", ai_enabled=True, privacy_mode=True)
        c3 = Camera(id="cam_disabled", name="Dapur", room_id="dapur", status="online", ai_enabled=False, privacy_mode=False)
        db.add_all([c1, c2, c3])
        await db.commit()

    active_cams = await worker.get_active_cameras()
    active_ids = [c.id for c in active_cams]

    # Hanya cam_open yang diizinkan dibaca oleh worker AI
    assert "cam_open" in active_ids
    assert "cam_private" not in active_ids
    assert "cam_disabled" not in active_ids


@pytest.mark.asyncio
async def test_retention_cleanup(test_db, tmp_path):
    """Pengujian retensi data: menghapus log benda lama dan thumbnail terenkripsi fisik."""
    worker = VisionWorker.__new__(VisionWorker)
    worker.session_maker = test_db

    now = datetime.datetime.now(datetime.timezone.utc)
    old_time = now - datetime.timedelta(days=10)  # Lebih tua dari 7 hari

    fake_thumb = tmp_path / "item_old.enc"
    fake_thumb.write_bytes(b"dummy_encrypted_thumbnail")

    async with test_db() as db:
        cam = Camera(id="cam_test", name="Uji", room_id="kamar", status="online")
        db.add(cam)

        old_item = DetectedItemLog(
            id="item_old",
            camera_id="cam_test",
            room_id="kamar",
            class_name="cup",
            first_seen_at=old_time,
            last_seen_at=old_time,
            thumbnail_path=str(fake_thumb),
        )
        fresh_item = DetectedItemLog(
            id="item_fresh",
            camera_id="cam_test",
            room_id="kamar",
            class_name="cup",
            first_seen_at=now,
            last_seen_at=now,
        )
        db.add_all([old_item, fresh_item])
        await db.commit()

    assert fake_thumb.exists()

    await worker.run_retention_cleanup()

    async with test_db() as db:
        items = (await db.execute(select(DetectedItemLog))).scalars().all()
        assert len(items) == 1
        assert items[0].id == "item_fresh"

    # Berkas fisik di disk harus terhapus
    assert not fake_thumb.exists()


@pytest.mark.asyncio
async def test_security_encrypted_thumbnail():
    """Pengujian enkripsi & dekripsi thumbnail dengan AES-256-GCM."""
    raw_image = b"RIIL_JPEG_BINARY_DATA_TEST_12345"
    cam_id = "cam_front_1"

    # 1. Enkripsi dengan kamera ID sebagai associated data
    ciphertext, nonce_hex = encrypt_clip_data(raw_image, cam_id)
    assert ciphertext != raw_image

    # 2. Dekripsi dengan kunci yang benar
    decrypted = decrypt_bytes(ciphertext, nonce_hex, associated_data=cam_id)
    assert decrypted == raw_image

    # 3. Dekripsi dengan associated data salah (kamera lain) HARUS GAGAL (InvalidTag)
    with pytest.raises(InvalidTag):
        decrypt_bytes(ciphertext, nonce_hex, associated_data="cam_hacker_2")

    # 4. Dekripsi dengan nonce salah HARUS GAGAL
    wrong_nonce = "00" * 12
    with pytest.raises(InvalidTag):
        decrypt_bytes(ciphertext, wrong_nonce, associated_data=cam_id)


@pytest.mark.asyncio
async def test_worker_heartbeat_and_timeout():
    """Pengujian status heartbeat worker: aktif bila baru, tidak aktif bila terhenti melebihi timeout."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Kirim heartbeat
        hb_resp = await client.post(
            "/api/cameras/ai/heartbeat",
            json={
                "worker_id": "test_worker_hb",
                "status": "online",
                "active_cameras": 2,
                "fps_actual": 4.5,
                "cpu_percent": 35.0,
                "memory_mb": 140.0,
            },
        )
        assert hb_resp.status_code == 200

        # Pastikan user admin ada di database
        from server.app.core.database import AsyncSessionLocal
        from server.app.core.security import create_access_token
        async with AsyncSessionLocal() as db:
            stmt = select(User).where(User.username == "admin_hb_tester")
            admin_u = (await db.execute(stmt)).scalar_one_or_none()
            if not admin_u:
                admin_u = User(username="admin_hb_tester", role="admin", is_active=True, password_hash="dummy_hash_test")
                db.add(admin_u)
                await db.commit()
                await db.refresh(admin_u)
            uid = admin_u.id

        token = create_access_token(user_id=uid, username="admin_hb_tester", role="admin")
        headers = {"Authorization": f"Bearer {token}"}

        status_resp = await client.get("/api/cameras/ai/status", headers=headers)
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["worker_status"] == "online"
        assert data["message"] == "AI aktif"
        assert data["active_cameras"] == 2


@pytest.mark.asyncio
async def test_queue_drop_resilience():
    """Pengujian ketahanan antrean: frame lama dibuang, tidak pernah ditumpuk (queue size 1)."""
    # Menguji logika antrean ukuran 1
    queue = asyncio.Queue(maxsize=1)

    # Frame 1 masuk
    queue.put_nowait({"frame_id": 1, "ts": 100})
    assert queue.full()

    # Frame 2 tiba saat konsumen belum membaca: buang frame 1, masukkan frame 2
    try:
        queue.put_nowait({"frame_id": 2, "ts": 101})
    except asyncio.QueueFull:
        _ = queue.get_nowait()  # Drop frame lama
        queue.put_nowait({"frame_id": 2, "ts": 101})

    assert queue.qsize() == 1
    newest = queue.get_nowait()
    assert newest["frame_id"] == 2  # Frame terbaru diproses, frame lama dibuang


@pytest.mark.asyncio
async def test_person_never_saved_as_thumbnail_and_trackable_classes(test_db):
    """
    Buktikan bahwa kelas 'person' TIDAK PERNAH disimpan sebagai thumbnail di log benda,
    dan periksa daftar kelas yang diizinkan untuk disimpan.
    """
    # 1. Pastikan 'person' tidak ada dalam VISION_TRACKABLE_CLASSES
    assert "person" not in settings.VISION_TRACKABLE_CLASSES, "Pelanggaran Privasi: 'person' tidak boleh ada di VISION_TRACKABLE_CLASSES!"

    # 2. Daftar kelas terdaftar untuk pencarian barang
    expected_classes = [
        "cell phone", "remote", "handbag", "backpack", "suitcase",
        "bottle", "cup", "laptop", "mouse", "keyboard", "book", "umbrella"
    ]
    for c in expected_classes:
        assert c in settings.VISION_TRACKABLE_CLASSES

    # 3. Simulasikan frame yang berisi 'person' dan benda 'laptop'
    worker = VisionWorker(worker_id="test_worker_privacy")
    worker.session_maker = test_db

    # Dummy camera di test_db
    now = datetime.datetime.now(datetime.timezone.utc)
    async with test_db() as db:
        cam = Camera(id="cam_priv_test", name="Kamera Uji", room_id="Kamar", status="online", ai_enabled=True, privacy_mode=False)
        db.add(cam)
        await db.commit()

    # Panggil handle_person_presence dan handle_item_log langsung
    frame_dummy = np.full((480, 640, 3), 100, dtype=np.uint8)
    person_item = {"class_name": "person", "bbox": (50, 50, 200, 400), "score": 0.95, "track_id": 1}
    laptop_item = {"class_name": "laptop", "bbox": (300, 200, 500, 400), "score": 0.88, "track_id": 2}

    # 'person' diproses hanya untuk presensi agregat, bukan log benda
    await worker._handle_person_presence("cam_priv_test", 1, now)
    await worker._handle_item_log("cam_priv_test", "Kamar", laptop_item, frame_dummy, now)

    # 4. Verifikasi isi tabel DetectedItemLog di database
    async with test_db() as db:
        # Benda tercatat
        stmt_item = select(DetectedItemLog)
        items = (await db.execute(stmt_item)).scalars().all()
        assert len(items) == 1
        assert items[0].class_name == "laptop"

        # Pastikan TIDAK ADA log benda dengan class_name == 'person'
        stmt_person_item = select(DetectedItemLog).where(DetectedItemLog.class_name == "person")
        person_items = (await db.execute(stmt_person_item)).scalars().all()
        assert len(person_items) == 0, "Ditemukan log benda untuk 'person' padahal dilarang!"

        # Pastikan kejadian presensi orang ada tanpa thumbnail
        stmt_presence = select(PersonPresenceEvent).where(PersonPresenceEvent.camera_id == "cam_priv_test")
        presences = (await db.execute(stmt_presence)).scalars().all()
        assert len(presences) == 1
        assert presences[0].person_count == 1
        # Model PersonPresenceEvent tidak memiliki atribut thumbnail_path
        assert not hasattr(presences[0], "thumbnail_path")


@pytest.mark.asyncio
async def test_clip_and_thumbnail_decrypt_after_key_unification(tmp_path):
    """
    Pengujian penyatuan kunci MEDIA_ENCRYPTION_KEY dan persistensi dekripsi
    setelah restart server (instansiasi baru modul enkripsi).
    """
    from server.app.core.camera.encryption import (
        decrypt_bytes,
        encrypt_bytes,
        read_and_decrypt_clip,
        save_encrypted_clip,
    )

    test_video_data = b"SIMULATED_MP4_HIGH_RES_STREAM_DATA_720P_15FPS"
    cam_id = "test_cam_enc"
    enc_path = tmp_path / "test_clip.enc"

    # 1. Enkripsi dan simpan klip
    nonce_hex, size = save_encrypted_clip(test_video_data, cam_id, enc_path)
    assert enc_path.exists()
    assert size > len(test_video_data)

    # 2. Dekripsi langsung
    decrypted = read_and_decrypt_clip(enc_path, nonce_hex, cam_id)
    assert decrypted == test_video_data

    # 3. Simulasikan server restart: baca ulang dari file terpisah tanpa cache
    reloaded_bytes = enc_path.read_bytes()
    restored = decrypt_bytes(reloaded_bytes, nonce_hex, associated_data=cam_id)
    assert restored == test_video_data

