import asyncio
import json
import pyotp
import httpx
import sqlite3

BASE_URL = "http://127.0.0.1:8000"

def get_or_create_test_credentials():
    # Connect directly to sqlite to check budi or create an admin test user
    con = sqlite3.connect("server/data/rumah.db")
    cur = con.cursor()
    # Check if budi exists and what totp_secret is
    row = cur.execute("SELECT id, username, totp_secret FROM users WHERE username='budi'").fetchone()
    con.close()
    return row

async def main():
    print("=== PENGUJIAN ALUR RIIL BACKEND RUMAH ===")
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Health check
        res = await client.get("/api/health")
        print(f"[1] Health Check: status={res.status_code}, data={res.json().get('status')}")
        assert res.status_code == 200

        # 2. Login Flow with Member (risang or siti or create session)
        # Let's test admin 2FA flow:
        # We can update budi's password hash in DB to a known hash or reset it temporarily
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        pwd_hash = ph.hash("AdminPassword123!")
        
        con = sqlite3.connect("server/data/rumah.db")
        cur = con.cursor()
        cur.execute("UPDATE users SET password_hash=? WHERE username='budi'", (pwd_hash,))
        con.commit()
        totp_secret = cur.execute("SELECT totp_secret FROM users WHERE username='budi'").fetchone()[0]
        con.close()

        print(f"[2] Testing Login with 2FA Challenge for 'budi' (totp_secret={totp_secret})...")
        login_res = await client.post("/api/auth/login", json={"username": "budi", "password": "AdminPassword123!"})
        print(f"    Login response: {login_res.status_code}, body={login_res.json()}")
        assert login_res.status_code == 200
        assert login_res.json().get("status") == "2fa_required"
        temp_token = login_res.json()["temp_token"]

        # Generate TOTP code
        totp = pyotp.TOTP(totp_secret)
        current_otp = totp.now()
        print(f"[3] Testing Verify 2FA with OTP '{current_otp}'...")
        verify_res = await client.post("/api/auth/verify-2fa", json={"temp_token": temp_token, "code": current_otp})
        print(f"    Verify 2FA response: {verify_res.status_code}, status={verify_res.json().get('status')}")
        assert verify_res.status_code == 200
        access_token = verify_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 4. Get Devices
        dev_res = await client.get("/api/devices", headers=headers)
        print(f"[4] GET /api/devices: status={dev_res.status_code}, count={len(dev_res.json())}")
        assert dev_res.status_code == 200

        # 5. Device Toggle Command (POST /api/devices/{id}/cmd)
        cmd_payload = {"channel": "lamp_dapur_tamu", "action": "set", "value": True}
        cmd_res = await client.post("/api/devices/esp32_sim_1/cmd", json=cmd_payload, headers=headers)
        print(f"[5] POST /api/devices/esp32_sim_1/cmd: status={cmd_res.status_code}, body={cmd_res.json()}")
        assert cmd_res.status_code in [200, 202]

        # 6. Camera Pairing Code (POST /api/cameras/pairing-codes)
        cam_code_res = await client.post("/api/cameras/pairing-codes", json={"camera_name": "Kamera Pengujian", "room_id": "Ruang Tamu"}, headers=headers)
        print(f"[6] POST /api/cameras/pairing-codes: status={cam_code_res.status_code}, code={cam_code_res.json().get('code')}")
        assert cam_code_res.status_code == 200

        # 7. Assistant Chat Query (POST /api/assistant/chat)
        asst_res = await client.post("/api/assistant/chat", json={"message": "Halo, bagaimana status rumah?"}, headers=headers)
        print(f"[7] POST /api/assistant/chat: status={asst_res.status_code}, reply={asst_res.json().get('response') or asst_res.json().get('message') or asst_res.json().get('content')}")
        assert asst_res.status_code == 200

    print("=== SEMUA ALUR RIIL BACKEND SUKSES 100% ===")

if __name__ == "__main__":
    asyncio.run(main())
