"""
Test End-to-End Live Hardware ESP32 (esp32_559ed8)
"""
import time
import httpx
import sqlite3

BASE_URL = "http://127.0.0.1:8000"
DEVICE_ID = "esp32_559ed8"

def login():
    res = httpx.post(f"{BASE_URL}/api/auth/login", json={"username": "risang", "password": "risang110920"})
    token = res.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}

def get_channel_value(channel_key):
    conn = sqlite3.connect("server/data/rumah.db")
    cur = conn.cursor()
    val = cur.execute("SELECT current_value FROM channels WHERE device_id = ? AND channel_key = ?", (DEVICE_ID, channel_key)).fetchone()
    conn.close()
    return val[0] if val else None

def get_latest_status():
    conn = sqlite3.connect("server/data/rumah.db")
    cur = conn.cursor()
    rows = cur.execute("SELECT channel_key, current_value, updated_at FROM channels WHERE device_id = ?", (DEVICE_ID,)).fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

def send_command(headers, channel, action, value):
    t0 = time.time()
    res = httpx.post(
        f"{BASE_URL}/api/devices/{DEVICE_ID}/cmd",
        json={"channel": channel, "action": action, "value": value},
        headers=headers,
        timeout=10.0
    )
    cmd_id = res.json().get("cmd_id")
    return cmd_id, t0

def wait_for_state(channel_key, expected_val, t0, timeout=8.0):
    expected_str = str(expected_val).lower()
    start = time.time()
    while time.time() - start < timeout:
        val = get_channel_value(channel_key)
        if val == expected_str:
            latency = (time.time() - t0) * 1000
            return True, latency
        time.sleep(0.3)
    return False, (time.time() - t0) * 1000

def run_tests():
    headers = login()
    results = []

    tests = [
        # (name, channel, action, value, check_key, expected_val, pin)
        ("Lampu Tengah ON", "lamp_tengah", "set", True, "lamp_tengah", "true", "GPIO 21"),
        ("Lampu Tengah OFF", "lamp_tengah", "set", False, "lamp_tengah", "false", "GPIO 21"),
        ("Lampu Dapur & Tamu ON", "lamp_dapur_tamu", "set", True, "lamp_dapur_tamu", "true", "GPIO 17"),
        ("Lampu Dapur & Tamu OFF", "lamp_dapur_tamu", "set", False, "lamp_dapur_tamu", "false", "GPIO 17"),
        ("Lampu Kamar ON", "lamp_kamar", "set", True, "lamp_kamar", "true", "GPIO 16"),
        ("Lampu Kamar OFF", "lamp_kamar", "set", False, "lamp_kamar", "false", "GPIO 16"),
        ("Semua Lampu ON", "lamp", "set", True, "lamp", "true", "GPIO 21,17,16"),
        ("Semua Lampu OFF", "lamp", "set", False, "lamp", "false", "GPIO 21,17,16"),
        ("Relay Kipas ON", "relay", "set", True, "relay", "true", "GPIO 32 (Aktif LOW)"),
        ("Relay Kipas OFF", "relay", "set", False, "relay", "false", "GPIO 32 (Aktif LOW)"),
        ("Semua Saklar ON (Termasuk Buzzer)", "all", "set", True, "lamp_tengah", "true", "Semua Pin Aktif"),
        ("Semua Saklar OFF", "all", "set", False, "lamp_tengah", "false", "Semua Pin Padam"),
    ]

    print("\n" + "=" * 75)
    print("  MEMULAI PENGUJIAN END-TO-END HARDWARE ESP32 SECARA LIVE")
    print(f"  Target: {DEVICE_ID} (IP: 192.168.1.27)")
    print("=" * 75)

    for name, ch, act, val, check_key, exp_val, pin in tests:
        print(f"\n[TEST] Mengirim: {name} (Channel: {ch}, Nilai: {val})...")
        cmd_id, t0 = send_command(headers, ch, act, val)
        ok, latency = wait_for_state(check_key, exp_val, t0)
        status_txt = "BERHASIL (ACK & Status OK)" if ok else "TIMEOUT / BELUM STATUS"
        print(f"       -> Status: {status_txt} | Latensi: {latency:.1f} ms | Pin: {pin}")
        results.append({
            "test": name,
            "channel": ch,
            "pin": pin,
            "cmd_id": cmd_id,
            "ok": ok,
            "latency": latency,
        })
        time.sleep(0.5)

    # Cek Pembacaan Sensor
    print("\n" + "=" * 75)
    print("  MEMERIKSA PEMBACAAN SENSOR REALTIME (MQ-2 & LDR)")
    print("=" * 75)
    status = get_latest_status()
    print("Status Telemetri Terakhir di Database:")
    for k, v in status.items():
        print(f"  - {k:18}: {v}")

    return results, status

if __name__ == "__main__":
    run_tests()
