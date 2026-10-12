import json
from httpx import ASGITransport, AsyncClient
import pyotp
import pytest
from sqlalchemy import text

from server.app.core.database import Base, engine, init_sqlite_wal
from server.app.core.setup_manager import (
    get_current_setup_code,
    reset_setup_code_for_testing,
)
from server.app.main import app


@pytest.fixture(autouse=True)
async def setup_clean_db():
    """Reset database tables before each test session."""
    await init_sqlite_wal()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    reset_setup_code_for_testing()
    yield


@pytest.mark.asyncio
async def test_setup_wizard_flow():
    async with AsyncClient(
        transport=ASGITransport(app=app, client=("127.0.0.1", 50000)),
        base_url="http://test",
    ) as client:
        # 1. Cek status setup awal
        res = await client.get("/api/auth/setup-status")
        assert res.status_code == 200
        assert res.json()["is_setup"] is False
        assert res.json()["setup_code_required"] is True

        code = get_current_setup_code()
        assert code is not None and code.startswith("RUMAH-")

        # 2. Coba daftar dengan kode salah -> gagal
        bad_res = await client.post(
            "/api/auth/setup-admin",
            json={
                "setup_code": "SALAH-1234",
                "username": "admin",
                "password": "PasswordAdmin123!",
            },
        )
        assert bad_res.status_code == 400

        # 3. Setup dengan kode yang benar -> sukses
        ok_res = await client.post(
            "/api/auth/setup-admin",
            json={
                "setup_code": code,
                "username": "admin",
                "password": "PasswordAdmin123!",
            },
        )
        assert ok_res.status_code == 201
        data = ok_res.json()
        assert data["status"] == "ok"
        assert data["user"]["role"] == "admin"
        assert "totp_secret" in data
        assert "totp_uri" in data
        assert len(data["recovery_codes"]) == 8

        # 4. Status setup sekarang True
        status_res = await client.get("/api/auth/setup-status")
        assert status_res.json()["is_setup"] is True

        # 5. Mencoba setup lagi -> ditolak
        dup_res = await client.post(
            "/api/auth/setup-admin",
            json={
                "setup_code": code,
                "username": "admin2",
                "password": "PasswordAdmin123!",
            },
        )
        assert dup_res.status_code == 400


@pytest.mark.asyncio
async def test_admin_login_totp_and_recovery_codes():
    async with AsyncClient(
        transport=ASGITransport(app=app, client=("127.0.0.1", 50000)),
        base_url="http://test",
    ) as client:
        # Inisialisasi admin
        await client.get("/api/auth/setup-status")
        code = get_current_setup_code()
        setup_res = await client.post(
            "/api/auth/setup-admin",
            json={
                "setup_code": code,
                "username": "admin",
                "password": "PasswordAdmin123!",
            },
        )
        totp_secret = setup_res.json()["totp_secret"]
        recovery_codes = setup_res.json()["recovery_codes"]

        # 1. Login kata sandi salah -> 401
        bad_pwd = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "SalahPassword123"},
        )
        assert bad_pwd.status_code == 401

        # 2. Login benar -> ditantang 2FA
        login_res = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "PasswordAdmin123!"},
        )
        assert login_res.status_code == 200
        assert login_res.json()["status"] == "2fa_required"
        temp_token = login_res.json()["temp_token"]

        # 3. Verifikasi 2FA dengan kode TOTP valid
        totp_code = pyotp.TOTP(totp_secret).now()
        v_res = await client.post(
            "/api/auth/verify-2fa",
            json={"temp_token": temp_token, "code": totp_code},
        )
        assert v_res.status_code == 200
        tokens = v_res.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        access_token = tokens["access_token"]

        # 4. Akses /me dengan access token
        me_res = await client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_res.status_code == 200
        assert me_res.json()["username"] == "admin"
        assert me_res.json()["role"] == "admin"

        # 5. Uji pemakaian recovery code saat login
        login_res2 = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "PasswordAdmin123!"},
        )
        temp_token2 = login_res2.json()["temp_token"]
        rec_code = recovery_codes[0]

        v_rec_res = await client.post(
            "/api/auth/verify-2fa",
            json={"temp_token": temp_token2, "code": rec_code},
        )
        assert v_rec_res.status_code == 200
        assert v_rec_res.json()["used_recovery_code"] is True

        # 6. Recovery code yang sama tidak bisa dipakai dua kali
        login_res3 = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "PasswordAdmin123!"},
        )
        temp_token3 = login_res3.json()["temp_token"]
        v_rec_fail = await client.post(
            "/api/auth/verify-2fa",
            json={"temp_token": temp_token3, "code": rec_code},
        )
        assert v_rec_fail.status_code == 401


@pytest.mark.asyncio
async def test_rbac_and_audit_logs():
    async with AsyncClient(
        transport=ASGITransport(app=app, client=("127.0.0.1", 50000)),
        base_url="http://test",
    ) as client:
        # Setup admin
        await client.get("/api/auth/setup-status")
        setup_code = get_current_setup_code()
        s_res = await client.post(
            "/api/auth/setup-admin",
            json={
                "setup_code": setup_code,
                "username": "admin",
                "password": "PasswordAdmin123!",
            },
        )
        totp_secret = s_res.json()["totp_secret"]

        # Login admin
        l_res = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "PasswordAdmin123!"},
        )
        temp_token = l_res.json()["temp_token"]
        v_res = await client.post(
            "/api/auth/verify-2fa",
            json={
                "temp_token": temp_token,
                "code": pyotp.TOTP(totp_secret).now(),
            },
        )
        admin_token = v_res.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 1. Admin membuat member dan child
        m_create = await client.post(
            "/api/auth/users",
            json={
                "username": "ibu_budi",
                "password": "MemberPassword123!",
                "role": "member",
            },
            headers=admin_headers,
        )
        assert m_create.status_code == 201

        c_create = await client.post(
            "/api/auth/users",
            json={
                "username": "anak_adi",
                "password": "ChildPassword123!",
                "role": "child",
            },
            headers=admin_headers,
        )
        assert c_create.status_code == 201

        # 2. Login member (tanpa 2FA)
        m_login = await client.post(
            "/api/auth/login",
            json={"username": "ibu_budi", "password": "MemberPassword123!"},
        )
        assert m_login.status_code == 200
        assert m_login.json()["status"] == "ok"
        member_token = m_login.json()["access_token"]
        member_headers = {"Authorization": f"Bearer {member_token}"}

        # 3. Login child (tanpa 2FA)
        c_login = await client.post(
            "/api/auth/login",
            json={"username": "anak_adi", "password": "ChildPassword123!"},
        )
        assert c_login.status_code == 200
        child_token = c_login.json()["access_token"]
        child_headers = {"Authorization": f"Bearer {child_token}"}

        # 4. Pengujian /api/test/admin-only
        assert (
            await client.get("/api/test/admin-only", headers=admin_headers)
        ).status_code == 200
        assert (
            await client.get("/api/test/admin-only", headers=member_headers)
        ).status_code == 403
        assert (
            await client.get("/api/test/admin-only", headers=child_headers)
        ).status_code == 403

        # 5. Pengujian /api/test/member-only
        assert (
            await client.get("/api/test/member-only", headers=admin_headers)
        ).status_code == 200
        assert (
            await client.get("/api/test/member-only", headers=member_headers)
        ).status_code == 200
        assert (
            await client.get("/api/test/member-only", headers=child_headers)
        ).status_code == 403

        # 6. Pengujian /api/test/child-allowed
        assert (
            await client.get("/api/test/child-allowed", headers=admin_headers)
        ).status_code == 200
        assert (
            await client.get("/api/test/child-allowed", headers=member_headers)
        ).status_code == 200
        assert (
            await client.get("/api/test/child-allowed", headers=child_headers)
        ).status_code == 200

        # 7. Audit log: Hanya admin yang dapat mengakses
        audit_admin = await client.get(
            "/api/audit-logs", headers=admin_headers
        )
        assert audit_admin.status_code == 200
        logs = audit_admin.json()["logs"]
        assert len(logs) >= 3
        actions = [log["action"] for log in logs]
        assert "auth.setup_admin" in actions
        assert "user.create" in actions

        audit_member = await client.get(
            "/api/audit-logs", headers=member_headers
        )
        assert audit_member.status_code == 403


@pytest.mark.asyncio
async def test_setup_wizard_rejects_proxy_headers():
    async with AsyncClient(
        transport=ASGITransport(app=app, client=("127.0.0.1", 50000)),
        base_url="http://test",
    ) as client:
        await client.get("/api/auth/setup-status")
        code = get_current_setup_code()
        assert code is not None

        # Coba akses dengan berbagai header reverse proxy/tunnel
        proxy_header_samples = [
            {"X-Forwarded-For": "203.0.113.195"},
            {"X-Real-IP": "198.51.100.1"},
            {"CF-Connecting-IP": "104.16.1.1"},
            {"Forwarded": "for=192.0.2.60;proto=http;by=203.0.113.43"},
            {"Via": "1.1 vegur"},
        ]

        for headers in proxy_header_samples:
            res = await client.post(
                "/api/auth/setup-admin",
                json={
                    "setup_code": code,
                    "username": "admin",
                    "password": "PasswordAdmin123!",
                },
                headers=headers,
            )
            assert res.status_code == 403, f"Harusnya ditolak untuk header {headers}"
            assert "reverse proxy" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_refresh_token_rotation():
    async with AsyncClient(
        transport=ASGITransport(app=app, client=("127.0.0.1", 50000)),
        base_url="http://test",
    ) as client:
        # Setup admin
        await client.get("/api/auth/setup-status")
        code = get_current_setup_code()
        s_res = await client.post(
            "/api/auth/setup-admin",
            json={
                "setup_code": code,
                "username": "admin",
                "password": "PasswordAdmin123!",
            },
        )
        totp_secret = s_res.json()["totp_secret"]

        # Login admin & verifikasi 2FA
        l_res = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "PasswordAdmin123!"},
        )
        temp_token = l_res.json()["temp_token"]
        v_res = await client.post(
            "/api/auth/verify-2fa",
            json={
                "temp_token": temp_token,
                "code": pyotp.TOTP(totp_secret).now(),
            },
        )
        assert v_res.status_code == 200
        initial_refresh_token = v_res.json()["refresh_token"]

        # 1. Gunakan refresh token pertama kali -> berhasil & menerima refresh token baru
        ref_res1 = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": initial_refresh_token},
        )
        assert ref_res1.status_code == 200
        ref_data1 = ref_res1.json()
        assert "access_token" in ref_data1
        assert "refresh_token" in ref_data1
        new_refresh_token = ref_data1["refresh_token"]
        assert new_refresh_token != initial_refresh_token

        # 2. Refresh token lama telah dicabut (revoked), tidak bisa dipakai lagi
        ref_old_res = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": initial_refresh_token},
        )
        assert ref_old_res.status_code == 401

        # 3. Refresh token baru yang baru dirotasi dapat digunakan
        ref_res2 = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": new_refresh_token},
        )
        assert ref_res2.status_code == 200
        ref_data2 = ref_res2.json()
        newer_refresh_token = ref_data2["refresh_token"]
        assert newer_refresh_token != new_refresh_token
