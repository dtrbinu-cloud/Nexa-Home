import asyncio
import hashlib
from pathlib import Path
import sys
import time

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import httpx
import jwt
from sqlalchemy import select

from server.app.core.config import settings
from server.app.core.database import async_session_factory, Base, engine
from server.app.models.camera import Camera, CameraToken
from server.app.models.user import User

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 1. Setup camera & user
    async with async_session_factory() as db:
        # User
        user = (await db.execute(select(User).where(User.username == "test_whep_user"))).scalar_one_or_none()
        if not user:
            user = User(
                username="test_whep_user",
                role="admin",
                is_active=True,
                password_hash="mock_hash",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Camera
        cam_id = "cam_auth_test"
        cam = (await db.execute(select(Camera).where(Camera.id == cam_id))).scalar_one_or_none()
        if not cam:
            cam = Camera(
                id=cam_id,
                name="Auth Test Cam",
                room_id="Lab",
                status="online",
                privacy_mode=False,
                ai_enabled=True,
            )
            db.add(cam)
            await db.commit()
            await db.refresh(cam)
        else:
            cam.privacy_mode = False
            await db.commit()

        user_id = user.id

    # Create valid JWT
    payload = {
        "sub": str(user_id),
        "email": "test_whep@rumah.local",
        "role": "admin",
        "exp": int(time.time()) + 3600,
    }
    valid_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    invalid_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.payload"

    print("=" * 65)
    print("PENGUJIAN OTORISASI WHEP MEDIAMTX (AUTH HOOK BACKEND)")
    print("=" * 65)
    print(f"Kamera ID   : {cam_id}")
    print(f"User ID     : {user_id}")
    print(f"Valid JWT   : {valid_jwt[:25]}... (panjang: {len(valid_jwt)})")
    print("-" * 65)

    auth_url = "http://127.0.0.1:8000/api/cameras/auth/mediamtx"

    # We can test either directly with httpx (if backend running) or via direct handler invocation
    # Let's test with FastAPI TestClient for deterministic, reproducible raw execution
    from fastapi.testclient import TestClient
    from server.app.main import app

    client = TestClient(app)

    # Test 1: Permintaan WHEP tanpa token
    res1 = client.post(
        "/api/cameras/auth/mediamtx",
        json={"action": "read", "path": cam_id, "ip": "127.0.0.1", "user": "", "password": ""}
    )
    print(f"[TEST 1] Permintaan WHEP Tanpa Token (Missing JWT):")
    print(f"  Status Code: {res1.status_code}")
    print(f"  Response   : {res1.json()}")
    assert res1.status_code == 401

    # Test 2: Permintaan WHEP dengan token salah / manipulasi
    res2 = client.post(
        "/api/cameras/auth/mediamtx",
        json={"action": "read", "path": cam_id, "ip": "127.0.0.1", "user": "", "password": invalid_jwt}
    )
    print(f"\n[TEST 2] Permintaan WHEP Dengan Token Tidak Valid (Fake/Tampered JWT):")
    print(f"  Status Code: {res2.status_code}")
    print(f"  Response   : {res2.json()}")
    assert res2.status_code == 401

    # Test 3: Permintaan WHEP dengan token JWT pengguna yang valid
    res3 = client.post(
        "/api/cameras/auth/mediamtx",
        json={"action": "read", "path": cam_id, "ip": "127.0.0.1", "user": "", "password": valid_jwt}
    )
    print(f"\n[TEST 3] Permintaan WHEP Dengan Token JWT Valid:")
    print(f"  Status Code: {res3.status_code}")
    assert res3.status_code == 200

    # Test 4: Kamera dalam mode privasi (privacy_mode=True)
    async with async_session_factory() as db:
        cam_db = (await db.execute(select(Camera).where(Camera.id == cam_id))).scalar_one()
        cam_db.privacy_mode = True
        await db.commit()

    res4 = client.post(
        "/api/cameras/auth/mediamtx",
        json={"action": "read", "path": cam_id, "ip": "127.0.0.1", "user": "", "password": valid_jwt}
    )
    print(f"\n[TEST 4] Permintaan WHEP Saat Kamera Mode Privasi Aktif:")
    print(f"  Status Code: {res4.status_code}")
    print(f"  Response   : {res4.json()}")
    assert res4.status_code == 403

    print("\n" + "=" * 65)
    print("KESIMPULAN: Seluruh permintaan WHEP tanpa JWT atau dengan token")
    print("palsu DITOLAK (HTTP 401). Hanya JWT valid yang diizinkan (HTTP 200).")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
