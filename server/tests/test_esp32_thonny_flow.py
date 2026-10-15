import datetime
from httpx import ASGITransport, AsyncClient
import pyotp
import pytest
from sqlalchemy import select

from server.app.core.database import AsyncSessionLocal, Base, engine, init_sqlite_wal
from server.app.core.device_queue import device_queue
from server.app.core.setup_manager import get_current_setup_code, reset_setup_code_for_testing
from server.app.main import app
from server.app.models.automation import NotificationLog
from server.app.models.device import Channel, Device, TelemetryLog
from server.app.models.user import User


@pytest.fixture(autouse=True)
async def setup_clean_db():
    await init_sqlite_wal()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    reset_setup_code_for_testing()
    device_queue.clear_device_queue("esp32_a4f210")
    yield


async def create_admin_and_login(client: AsyncClient):
    await client.get("/api/auth/setup-status")
    code = get_current_setup_code()
    s_res = await client.post(
        "/api/auth/setup-admin",
        json={"setup_code": code, "username": "admin", "password": "PasswordAdmin123!"},
    )
    totp_secret = s_res.json()["totp_secret"]

    l_res = await client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "PasswordAdmin123!"},
    )
    v_res = await client.post(
        "/api/auth/verify-2fa",
        json={"temp_token": l_res.json()["temp_token"], "code": pyotp.TOTP(totp_secret).now()},
    )
    return v_res.json()["access_token"]


@pytest.mark.asyncio
async def test_esp32_thonny_complete_lifecycle():
    """
    Simulasi alur lengkap MicroPython esp32_thonny.py:
    1. ESP32 mengirim status awal (POST /api/device/status) dengan PAIR_CODE 6-digit.
    2. User di Web / Flutter mengklaim perangkat dengan PAIR_CODE 6-digit.
    3. User menyalakan 'lamp_kamar' dan 'relay' dari UI / API.
    4. ESP32 menarik antrean perintah (POST /api/device/poll) dan menerima 'lamp_kamar_on' serta 'relay_on'.
    5. ESP32 mengirim konfirmasi eksekusi (POST /api/device/ack).
    6. ESP32 memperbarui status terkini (POST /api/device/status).
    7. ESP32 memicu simulasi sensor gas darurat (MQ-2 >= 1500) dan memastikan notifikasi bahaya tercatat.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app, client=("127.0.0.1", 50000)),
        base_url="http://test",
    ) as client:
        device_id = "esp32_a4f210"
        device_key = "key_a4f210"
        pair_code = "654321"

        # ----------------------------------------------------------------------
        # Langkah 1: ESP32 Booting dan Mengirim Laporan Status Awal
        # ----------------------------------------------------------------------
        boot_status_payload = {
            "device_id": device_id,
            "device_key": device_key,
            "pair_code": pair_code,
            "status": {
                "lamp": 0,
                "lamp_tengah": 0,
                "lamp_dapur_tamu": 0,
                "lamp_kamar": 0,
                "relay": 0,
                "gas_raw": 180,
                "gas_pct": 4,
                "gas_alarm": 0,
                "gas_threshold": 1500,
                "ldr": 850,
                "ldr_pct": 20,
                "ldr_mode": "analog",
                "is_dark": 0,
                "ip": "192.168.1.105",
                "uptime_s": 5,
            },
        }

        status_res = await client.post("/api/device/status", json=boot_status_payload)
        assert status_res.status_code == 200
        assert status_res.json() == {"ok": True}

        # Verifikasi perangkat & kanal tersimpan di database
        async with AsyncSessionLocal() as session:
            dev = (await session.execute(select(Device).where(Device.id == device_id))).scalar_one_or_none()
            assert dev is not None
            assert dev.is_online is True
            assert dev.ip_address == "192.168.1.105"

            chans = (await session.execute(select(Channel).where(Channel.device_id == device_id))).scalars().all()
            chan_keys = {c.channel_key for c in chans}
            assert "lamp_kamar" in chan_keys
            assert "lamp_tengah" in chan_keys
            assert "lamp_dapur_tamu" in chan_keys
            assert "relay" in chan_keys
            assert "mq2" in chan_keys
            assert "ldr" in chan_keys

        # ----------------------------------------------------------------------
        # Langkah 2: User Login dan Mengklaim Perangkat menggunakan 6-Digit PAIR_CODE
        # ----------------------------------------------------------------------
        token = await create_admin_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        claim_res = await client.post(
            "/api/devices/claim",
            headers=headers,
            json={
                "claim_token": pair_code,  # 6-digit pair code dari layar Thonny
                "name": "ESP32 Rumah Utama",
                "room": "Ruang Tamu",
            },
        )
        assert claim_res.status_code == 200
        claim_data = claim_res.json()
        assert claim_data["status"] == "ok"
        assert claim_data["device"]["id"] == device_id
        assert claim_data["device"]["name"] == "ESP32 Rumah Utama"

        # ----------------------------------------------------------------------
        # Langkah 3: User Menekan Saklar 'lamp_kamar' dan 'relay' dari UI Web / App
        # ----------------------------------------------------------------------
        cmd1_res = await client.post(
            f"/api/devices/{device_id}/cmd",
            headers=headers,
            json={"channel": "lamp_kamar", "action": "set", "value": True},
        )
        assert cmd1_res.status_code == 200
        cmd1_id = cmd1_res.json()["cmd_id"]

        cmd2_res = await client.post(
            f"/api/devices/{device_id}/cmd",
            headers=headers,
            json={"channel": "relay", "action": "set", "value": True},
        )
        assert cmd2_res.status_code == 200
        cmd2_id = cmd2_res.json()["cmd_id"]

        # ----------------------------------------------------------------------
        # Langkah 4: ESP32 Memanggil Polling (POST /api/device/poll)
        # ----------------------------------------------------------------------
        poll_res = await client.post(
            "/api/device/poll",
            json={"device_id": device_id, "device_key": device_key, "limit": 5},
        )
        assert poll_res.status_code == 200
        poll_data = poll_res.json()
        assert poll_data["ok"] is True
        commands = poll_data["commands"]
        assert len(commands) == 2

        cmds_dict = {c["id"]: c["cmd"] for c in commands}
        assert cmd1_id in cmds_dict
        assert cmds_dict[cmd1_id] == "lamp_kamar_on"
        assert cmd2_id in cmds_dict
        assert cmds_dict[cmd2_id] == "relay_on"

        # ----------------------------------------------------------------------
        # Langkah 5: ESP32 Mengirim Konfirmasi Eksekusi (POST /api/device/ack)
        # ----------------------------------------------------------------------
        ack1_res = await client.post(
            "/api/device/ack",
            json={"device_id": device_id, "device_key": device_key, "command_id": cmd1_id, "ok": True},
        )
        assert ack1_res.status_code == 200
        assert ack1_res.json()["ok"] is True

        ack2_res = await client.post(
            "/api/device/ack",
            json={"device_id": device_id, "device_key": device_key, "command_id": cmd2_id, "ok": True},
        )
        assert ack2_res.status_code == 200
        assert ack2_res.json()["ok"] is True

        # Polling lagi: Antrean sekarang harus kosong
        poll2_res = await client.post(
            "/api/device/poll",
            json={"device_id": device_id, "device_key": device_key, "limit": 5},
        )
        assert poll2_res.json()["commands"] == []

        # ----------------------------------------------------------------------
        # Langkah 6: ESP32 Mengirim Pembaruan Status Terkini
        # ----------------------------------------------------------------------
        updated_status_payload = {
            "device_id": device_id,
            "device_key": device_key,
            "pair_code": pair_code,
            "status": {
                "lamp": 1,
                "lamp_tengah": 0,
                "lamp_dapur_tamu": 0,
                "lamp_kamar": 1,
                "relay": 1,
                "gas_raw": 210,
                "gas_pct": 5,
                "gas_alarm": 0,
                "gas_threshold": 1500,
                "ldr": 920,
                "ldr_pct": 22,
                "ldr_mode": "analog",
                "is_dark": 0,
                "ip": "192.168.1.105",
                "uptime_s": 25,
            },
        }
        status2_res = await client.post("/api/device/status", json=updated_status_payload)
        assert status2_res.status_code == 200

        # Verifikasi status kanal di DB telah sinkron
        async with AsyncSessionLocal() as session:
            kamar_ch = (await session.execute(
                select(Channel).where(Channel.device_id == device_id, Channel.channel_key == "lamp_kamar")
            )).scalar_one_or_none()
            assert kamar_ch.current_value == "true"

            relay_ch = (await session.execute(
                select(Channel).where(Channel.device_id == device_id, Channel.channel_key == "relay")
            )).scalar_one_or_none()
            assert relay_ch.current_value == "true"

        # ----------------------------------------------------------------------
        # Langkah 7: Uji Simulasi Bahaya Kebocoran Gas (MQ-2 >= 1500)
        # ----------------------------------------------------------------------
        gas_danger_payload = {
            "device_id": device_id,
            "device_key": device_key,
            "pair_code": pair_code,
            "status": {
                "lamp": 1,
                "lamp_tengah": 0,
                "lamp_dapur_tamu": 0,
                "lamp_kamar": 1,
                "relay": 1,
                "gas_raw": 1820,
                "gas_pct": 44,
                "gas_alarm": 1,  # ALARM GAS AKTIF!
                "gas_threshold": 1500,
                "ldr": 900,
                "ldr_pct": 22,
                "ldr_mode": "analog",
                "is_dark": 0,
                "ip": "192.168.1.105",
                "uptime_s": 35,
            },
        }
        gas_res = await client.post("/api/device/status", json=gas_danger_payload)
        assert gas_res.status_code == 200

        # Verifikasi log notifikasi darurat dibuat
        async with AsyncSessionLocal() as session:
            notif = (await session.execute(
                select(NotificationLog).where(
                    NotificationLog.device_id == device_id,
                    NotificationLog.event_type == "gas_leak_alarm",
                )
            )).scalar_one_or_none()
            assert notif is not None
            assert notif.severity == "critical"
            assert "1820" in notif.message
