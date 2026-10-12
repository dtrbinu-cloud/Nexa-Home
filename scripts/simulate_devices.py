#!/usr/bin/env python3
"""
scripts/simulate_devices.py — Simulator Perangkat ESP32 via MQTT untuk Smart Home 'Rumah'.
Meniru perilaku ESP32 asli: LWT, publish state, respon terhadap command, dan pengiriman telemetri.
"""

import argparse
import json
import logging
import random
import signal
import sys
import time
from typing import Dict, List
import paho.mqtt.client as mqtt

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("simulator")


class SimulatedEsp32:
    def __init__(
        self,
        device_id: str,
        broker_host: str = "127.0.0.1",
        broker_port: int = 1883,
        username: str = "",
        password: str = "",
    ):
        self.device_id = device_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.running = False

        # Status kanal awal
        self.channels = {
            "lamp_tengah": False,
            "lamp_dapur_tamu": False,
            "lamp_kamar": False,
            "relay_fan": False,
            "buzzer": False,
        }

        # Status sensor awal
        self.gas_raw = 420.0
        self.is_dark = False

        self.client: mqtt.Client = None

    def start(self):
        self.running = True
        client_id = f"sim_{self.device_id}_{random.randint(1000, 9999)}"
        try:
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=client_id,
            )
        except Exception:
            self.client = mqtt.Client(client_id=client_id)

        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        # Pasang LWT (Last Will and Testament)
        avail_topic = f"home/{self.device_id}/availability"
        self.client.will_set(avail_topic, payload="offline", qos=1, retain=True)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=30)
            self.client.loop_start()
        except Exception as e:
            logger.warning("[%s] Gagal terhubung ke broker MQTT: %s", self.device_id, e)

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        logger.info("[%s] Terhubung ke broker MQTT! Mengirim LWT online...", self.device_id)
        # Publish online availability
        avail_topic = f"home/{self.device_id}/availability"
        client.publish(avail_topic, payload="online", qos=1, retain=True)

        # Subscribe ke perintah
        cmd_topic = f"home/{self.device_id}/cmd"
        client.subscribe(cmd_topic, qos=1)

        # Kirim state awal
        self.publish_state()

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            cmd_id = payload.get("id", "unknown")
            channel = payload.get("channel")
            action = payload.get("action", "set")
            value = payload.get("value")

            logger.info("[%s] Menerima Perintah CMD: %s -> %s = %s", self.device_id, channel, action, value)

            if channel in self.channels:
                if action == "toggle":
                    self.channels[channel] = not self.channels[channel]
                elif action == "set":
                    self.channels[channel] = bool(value)

                # Kirim ack
                ack_topic = f"home/{self.device_id}/ack"
                client.publish(
                    ack_topic,
                    json.dumps({"id": cmd_id, "status": "ok", "channel": channel, "current": self.channels[channel]}),
                    qos=1,
                )

                # Kirim state terbaru segera setelah aksi
                self.publish_state()
        except Exception as e:
            logger.error("[%s] Gagal memproses perintah: %s", self.device_id, e)

    def publish_state(self):
        if not self.client:
            return

        # Variasi nilai sensor secara realistis
        self.gas_raw = max(300.0, min(600.0, self.gas_raw + random.uniform(-15.0, 15.0)))

        state_payload = {
            "channels": self.channels,
            "sensors": {
                "gas_raw": round(self.gas_raw, 1),
                "is_dark": self.is_dark,
            },
            "ts": int(time.time()),
        }

        topic = f"home/{self.device_id}/state"
        self.client.publish(topic, json.dumps(state_payload), qos=1, retain=True)

    def stop(self):
        self.running = False
        if self.client:
            avail_topic = f"home/{self.device_id}/availability"
            self.client.publish(avail_topic, payload="offline", qos=1, retain=True)
            self.client.loop_stop()
            self.client.disconnect()


def main():
    parser = argparse.ArgumentParser(description="Simulator Perangkat ESP32 Smart Home")
    parser.add_argument("--count", type=int, default=1, help="Jumlah perangkat yang disimulasikan (default: 1)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host MQTT broker")
    parser.add_argument("--port", type=int, default=1883, help="Port MQTT broker")
    parser.add_argument("--user", type=str, default="rumah_server", help="MQTT username")
    parser.add_argument("--pwd", type=str, default="", help="MQTT password")
    args = parser.parse_args()

    devices: List[SimulatedEsp32] = []
    logger.info("Memulai simulator untuk %d perangkat ESP32...", args.count)

    for i in range(1, args.count + 1):
        dev_id = f"esp32_sim_{i}"
        dev = SimulatedEsp32(
            device_id=dev_id,
            broker_host=args.host,
            broker_port=args.port,
            username=args.user,
            password=args.pwd,
        )
        devices.append(dev)
        dev.start()

    def signal_handler(sig, frame):
        logger.info("\nMenghentikan semua perangkat simulator...")
        for d in devices:
            d.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        while True:
            time.sleep(5)
            for d in devices:
                d.publish_state()
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
