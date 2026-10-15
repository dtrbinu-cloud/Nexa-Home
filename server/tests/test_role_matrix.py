import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from server.app.main import app
from server.app.core.database import AsyncSessionLocal
from server.app.core.security import create_access_token, hash_password
from server.app.models.user import User
from server.app.models.automation import NotificationLog


@pytest.mark.asyncio
async def test_security_headers_present():
    """Memverifikasi bahwa HTTP Security Headers ketat Tahap 7 terpasang pada respon."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/health")
        assert res.status_code == 200
        headers = res.headers
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "max-age=31536000" in headers.get("Strict-Transport-Security", "")
        assert "Content-Security-Policy" in headers
        csp = headers.get("Content-Security-Policy")
        assert "default-src 'self'" in csp
        assert "accounts.google.com" in csp


@pytest.mark.asyncio
async def test_account_lockout_after_five_failed_attempts():
    """Memverifikasi bahwa akun terkunci otomatis selama 15 menit setelah 5x gagal login berturut-turut."""
    uid = uuid.uuid4().hex[:6]
    uname = f"lockuser_{uid}"
    email = f"lockuser_{uid}@example.com"
    pwd = "SecurePassword123!"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register user
        reg_res = await ac.post(
            "/api/auth/register",
            json={"full_name": "Lock Target", "username": uname, "email": email, "password": pwd},
        )
        assert reg_res.status_code == 201

        # Coba salah password 4 kali berturut-turut -> status 401
        for i in range(1, 5):
            res = await ac.post("/api/auth/login", json={"username": uname, "password": "WrongPassword!"})
            assert res.status_code == 401, f"Attempt {i} should be 401"

        # Percobaan ke-5 -> memicu status 403 Forbidden (Akun terkunci)
        res5 = await ac.post("/api/auth/login", json={"username": uname, "password": "WrongPassword!"})
        assert res5.status_code == 403
        data5 = res5.json()
        assert "kunci" in data5["detail"].lower()

        # Percobaan ke-6 (bahkan dengan password yang benar) tetap ditolak 403 karena akun sedang terkunci!
        res6 = await ac.post("/api/auth/login", json={"username": uname, "password": pwd})
        assert res6.status_code == 403
        data6 = res6.json()
        assert "kunci" in data6["detail"].lower()


@pytest.mark.asyncio
async def test_new_login_notification_created():
    """Memverifikasi bahwa login dari IP baru mencatat entri di tabel notifikasi."""
    uid = uuid.uuid4().hex[:6]
    uname = f"notifuser_{uid}"
    email = f"notif_{uid}@example.com"
    pwd = "MySecretPass123!"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/api/auth/register",
            json={"full_name": "Notif User", "username": uname, "email": email, "password": pwd},
        )

        # Login berhasil
        l_res = await ac.post("/api/auth/login", json={"username": uname, "password": pwd})
        assert l_res.status_code == 200

        # Verifikasi notifikasi login tersimpan di database
        async with AsyncSessionLocal() as session:
            q = select(NotificationLog).where(
                NotificationLog.event_type == "auth_login_new",
                NotificationLog.message.like(f"%{uname}%"),
            )
            res = await session.execute(q)
            notif = res.scalars().first()
            assert notif is not None
            assert uname in notif.message


@pytest.mark.asyncio
async def test_role_based_access_matrix():
    """Memverifikasi matriks izin akses untuk Admin, Member, Child, dan Pengguna Belum Disetujui."""
    uid = uuid.uuid4().hex[:6]
    async with AsyncSessionLocal() as session:
        # Buat entitas pengujian langsung di database
        admin_u = User(
            username=f"adm_{uid}",
            email=f"adm_{uid}@test.id",
            password_hash=hash_password("adminpass"),
            role="admin",
            is_active=True,
            is_approved=True,
        )
        member_u = User(
            username=f"mem_{uid}",
            email=f"mem_{uid}@test.id",
            password_hash=hash_password("memberpass"),
            role="member",
            is_active=True,
            is_approved=True,
        )
        child_u = User(
            username=f"chd_{uid}",
            email=f"chd_{uid}@test.id",
            password_hash=hash_password("childpass"),
            role="child",
            is_active=True,
            is_approved=True,
        )
        unappr_u = User(
            username=f"unp_{uid}",
            email=f"unp_{uid}@test.id",
            password_hash=hash_password("unapprpass"),
            role="member",
            is_active=True,
            is_approved=False,
        )
        session.add_all([admin_u, member_u, child_u, unappr_u])
        await session.commit()
        await session.refresh(admin_u)
        await session.refresh(member_u)
        await session.refresh(child_u)
        await session.refresh(unappr_u)

        admin_token = create_access_token(admin_u.id, admin_u.username, "admin")
        member_token = create_access_token(member_u.id, member_u.username, "member")
        child_token = create_access_token(child_u.id, child_u.username, "child")
        unappr_token = create_access_token(unappr_u.id, unappr_u.username, "member")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Endpoint Audit Logs (Hanya Admin)
        r_adm_audit = await ac.get("/api/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
        assert r_adm_audit.status_code == 200

        r_mem_audit = await ac.get("/api/audit-logs", headers={"Authorization": f"Bearer {member_token}"})
        assert r_mem_audit.status_code == 403

        r_chd_audit = await ac.get("/api/audit-logs", headers={"Authorization": f"Bearer {child_token}"})
        assert r_chd_audit.status_code == 403

        # 2. Endpoint Pending Users (Hanya Admin)
        r_adm_pending = await ac.get("/api/auth/pending-users", headers={"Authorization": f"Bearer {admin_token}"})
        assert r_adm_pending.status_code == 200

        r_mem_pending = await ac.get("/api/auth/pending-users", headers={"Authorization": f"Bearer {member_token}"})
        assert r_mem_pending.status_code == 403

        # 3. Endpoint Kamera (Admin & Member berhak, Child tidak boleh modifikasi atau akses langsung)
        r_adm_cam = await ac.get("/api/cameras", headers={"Authorization": f"Bearer {admin_token}"})
        assert r_adm_cam.status_code == 200

        r_mem_cam = await ac.get("/api/cameras", headers={"Authorization": f"Bearer {member_token}"})
        assert r_mem_cam.status_code == 200

        # 4. Status akun unapproved
        r_unp_me = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {unappr_token}"})
        assert r_unp_me.status_code == 200
        assert r_unp_me.json()["is_approved"] is False
