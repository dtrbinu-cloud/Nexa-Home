import os
from pathlib import Path
import socket
import subprocess
import time
import paho.mqtt.client as mqtt
import pytest

from server.app.core.mqtt_auth import hash_mosquitto_password

MOSQ_BIN = r"C:\Program Files\mosquitto\mosquitto.exe"


def get_lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


@pytest.fixture(scope="module")
def live_mosquitto(tmp_path_factory):
    """Spawns an isolated real Mosquitto broker instance listening on 0.0.0.0 and tested via LAN IP."""
    if not Path(MOSQ_BIN).exists():
        pytest.skip("Mosquitto executable not found at C:\\Program Files\\mosquitto\\mosquitto.exe")

    tmp_dir = tmp_path_factory.mktemp("mosq_test")
    conf_file = tmp_dir / "mosquitto.conf"
    passwd_file = tmp_dir / "mosquitto.passwd"
    acl_file = tmp_dir / "mosquitto.acl"

    test_port = 18883

    # Buat akun: backend_admin, device_a, device_b
    users = {
        "backend_admin": "backend_secret_123",
        "device_a": "dev_a_secret_pass",
        "device_b": "dev_b_secret_pass",
    }

    passwd_lines = [f"{u}:{hash_mosquitto_password(p)}" for u, p in users.items()]
    passwd_file.write_text("\n".join(passwd_lines) + "\n", encoding="utf-8")

    # ACL rules
    acl_content = f"""# Test Mosquitto ACL
user backend_admin
topic readwrite #

user device_a
topic readwrite home/device_a/#

user device_b
topic readwrite home/device_b/#
"""
    acl_file.write_text(acl_content, encoding="utf-8")

    # Config: Listener mendengarkan di seluruh antarmuka LAN (0.0.0.0)
    conf_content = f"""# Isolated Test Config
listener {test_port} 0.0.0.0
allow_anonymous false
password_file {passwd_file.as_posix()}
acl_file {acl_file.as_posix()}
persistence false
"""
    conf_file.write_text(conf_content, encoding="utf-8")

    proc = subprocess.Popen(
        [MOSQ_BIN, "-c", str(conf_file)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1.0)  # Beri waktu broker untuk bind socket

    lan_ip = get_lan_ip()
    yield {
        "port": test_port,
        "host": lan_ip,
        "users": users,
    }

    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()


def test_anonymous_connection_rejected(live_mosquitto):
    """(b) Koneksi tanpa kredensial ditolak (allow_anonymous false)."""
    conn_result = {"rc": None}

    def on_connect(c, ud, flags, rc, props=None):
        conn_result["rc"] = rc

    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect

    try:
        client.connect(live_mosquitto["host"], live_mosquitto["port"], keepalive=5)
        client.loop(timeout=2.0)
    except Exception:
        pass

    # Harus gagal atau mengembalikan rc != 0 (not authorized)
    assert conn_result["rc"] is None or conn_result["rc"] != 0


def test_wrong_password_rejected(live_mosquitto):
    """(a) Login dengan password salah ditolak."""
    conn_result = {"rc": None}

    def on_connect(c, ud, flags, rc, props=None):
        conn_result["rc"] = rc

    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set("device_a", "SALAH_PASSWORD_123")
    client.on_connect = on_connect

    try:
        client.connect(live_mosquitto["host"], live_mosquitto["port"], keepalive=5)
        client.loop(timeout=2.0)
    except Exception:
        pass

    # Harus gagal (rc != 0 atau connection refused)
    assert conn_result["rc"] is None or conn_result["rc"] != 0


def test_device_acl_isolation(live_mosquitto):
    """(c) Perangkat A tidak bisa publish atau subscribe ke topik Perangkat B."""
    client_a = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="test_client_a")
    client_a.username_pw_set("device_a", live_mosquitto["users"]["device_a"])

    client_b = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="test_client_b")
    client_b.username_pw_set("device_b", live_mosquitto["users"]["device_b"])

    msgs_a = []
    msgs_b = []

    client_a.on_message = lambda c, ud, msg: msgs_a.append((msg.topic, msg.payload.decode()))
    client_b.on_message = lambda c, ud, msg: msgs_b.append((msg.topic, msg.payload.decode()))

    client_a.connect(live_mosquitto["host"], live_mosquitto["port"], keepalive=10)
    client_b.connect(live_mosquitto["host"], live_mosquitto["port"], keepalive=10)

    client_a.loop_start()
    client_b.loop_start()
    time.sleep(0.5)

    # Device B subscribe ke topiknya sendiri
    client_b.subscribe("home/device_b/#", qos=1)
    # Device A subscribe ke topiknya sendiri dan coba subscribe ke Device B
    client_a.subscribe("home/device_a/#", qos=1)
    client_a.subscribe("home/device_b/#", qos=1)
    time.sleep(0.5)

    # 1. Device A mencoba publish ke topik Device B -> ACL menolak delivery ke Device B
    client_a.publish("home/device_b/cmd", '{"malicious":"injection"}', qos=1)
    time.sleep(0.5)
    # Device B tidak boleh menerima pesan dari Device A karena Device A tidak diizinkan publish ke home/device_b/#
    assert len(msgs_b) == 0

    # 2. Device B publish ke topiknya sendiri -> Device B menerima, tetapi Device A TIDAK menerima karena ACL melarang Device A membaca home/device_b/#
    client_b.publish("home/device_b/state", '{"state":"ok"}', qos=1)
    time.sleep(0.5)
    assert len(msgs_b) == 1
    assert msgs_b[0][0] == "home/device_b/state"
    # Device A tidak menerima pesan dari Device B meskipun mencoba subscribe
    assert len(msgs_a) == 0

    # 3. Device A publish ke topiknya sendiri -> Device A menerima
    client_a.publish("home/device_a/state", '{"state":"a_ok"}', qos=1)
    time.sleep(0.5)
    assert len(msgs_a) == 1
    assert msgs_a[0][0] == "home/device_a/state"

    client_a.loop_stop()
    client_b.loop_stop()
    client_a.disconnect()
    client_b.disconnect()


def test_backend_full_access(live_mosquitto):
    """(d) Akun backend bisa mengakses dan mengontrol semuanya (#)."""
    backend = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="test_backend")
    backend.username_pw_set("backend_admin", live_mosquitto["users"]["backend_admin"])

    connected = {"status": False}
    sub_granted = {"qos": None}
    received_msgs = []

    def on_connect(c, ud, flags, rc, props=None):
        if rc == 0:
            connected["status"] = True

    def on_subscribe(c, ud, mid, granted_qos, props=None):
        sub_granted["qos"] = granted_qos

    def on_message(c, ud, msg):
        received_msgs.append((msg.topic, msg.payload.decode()))

    backend.on_connect = on_connect
    backend.on_subscribe = on_subscribe
    backend.on_message = on_message

    backend.connect(live_mosquitto["host"], live_mosquitto["port"], keepalive=10)
    backend.loop_start()
    time.sleep(0.5)
    assert connected["status"] is True

    # Backend subscribe ke root '#' -> berhasil penuh tanpa penolakan
    backend.subscribe("#", qos=1)
    time.sleep(0.5)
    assert sub_granted["qos"] is not None and sub_granted["qos"][0] != 128

    # Backend publish ke Device A dan Device B -> sukses
    pub_info_a = backend.publish("home/device_a/cmd", '{"action":"set"}', qos=1)
    pub_info_b = backend.publish("home/device_b/cmd", '{"action":"set"}', qos=1)
    pub_info_a.wait_for_publish(timeout=2.0)
    pub_info_b.wait_for_publish(timeout=2.0)
    assert pub_info_a.is_published()
    assert pub_info_b.is_published()

    time.sleep(0.5)
    backend.loop_stop()
    backend.disconnect()
