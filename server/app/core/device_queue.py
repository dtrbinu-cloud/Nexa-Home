import datetime
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("server.device_queue")


class DeviceCommandQueue:
    """
    In-memory thread-safe command queue & pair code registry for ESP32 devices.
    Bridges Web, Flutter App, AI Assistant, and MicroPython HTTP polling.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # device_id -> list of pending command dicts
        self._queues: Dict[str, List[Dict[str, Any]]] = {}
        # pair_code (str) -> dict info
        self._pair_codes: Dict[str, Dict[str, Any]] = {}
        # command_id -> dict info
        self._acked_commands: Dict[str, Dict[str, Any]] = {}

    def register_pair_code(
        self,
        pair_code: str,
        device_id: str,
        device_key: Optional[str] = None,
        status: Optional[Dict[str, Any]] = None,
    ):
        """Register or update an active 6-digit pair code for a device."""
        if not pair_code:
            return
        code_str = str(pair_code).strip()
        with self._lock:
            self._pair_codes[code_str] = {
                "pair_code": code_str,
                "device_id": device_id,
                "device_key": device_key,
                "status": status or {},
                "updated_at": time.time(),
            }
            logger.info("Registered pair code '%s' for device '%s'", code_str, device_id)

    def resolve_pair_code(self, code_or_token: str) -> Optional[Dict[str, Any]]:
        """Look up device info by 6-digit pair code or token."""
        code_str = str(code_or_token).strip()
        with self._lock:
            # 1. Exact match by pair_code
            if code_str in self._pair_codes:
                entry = self._pair_codes[code_str]
                # Valid for 30 minutes
                if time.time() - entry.get("updated_at", 0) < 1800:
                    return entry

            # 2. Check if device_key or device_id matches
            for p_code, entry in self._pair_codes.items():
                if entry.get("device_id") == code_str or entry.get("device_key") == code_str:
                    return entry

        return None

    def enqueue_command(
        self,
        device_id: str,
        cmd_payload: Dict[str, Any],
    ) -> str:
        """
        Enqueue a command for a device.
        Automatically derives clean MicroPython string commands (e.g. 'lamp_kamar_on').
        """
        cmd_id = cmd_payload.get("id") or f"cmd_{int(time.time() * 1000)}"
        channel = str(cmd_payload.get("channel", "")).strip().lower()
        action = str(cmd_payload.get("action", "set")).strip().lower()
        value = cmd_payload.get("value")

        # Determine boolean state
        if isinstance(value, bool):
            is_on = value
        elif isinstance(value, (int, float)):
            is_on = value > 0
        elif isinstance(value, str):
            is_on = value.lower() in ("true", "1", "on", "yes")
        else:
            is_on = action in ("on", "turn_on", "activate")

        # Map channel + is_on to exact MicroPython string command
        cmd_str = self._resolve_cmd_string(channel, is_on, action)

        item = {
            "id": cmd_id,
            "cmd": cmd_str,
            "channel": channel,
            "action": action,
            "value": is_on,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }

        with self._lock:
            if device_id not in self._queues:
                self._queues[device_id] = []
            # Avoid duplicate unacked command for exact same channel
            self._queues[device_id] = [
                c for c in self._queues[device_id] if c.get("channel") != channel or c.get("id") == cmd_id
            ]
            self._queues[device_id].append(item)
            logger.info("Enqueued command for [%s]: %s (cmd_id=%s)", device_id, cmd_str, cmd_id)

        return cmd_id

    def get_pending_commands(self, device_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch pending commands for device_id."""
        with self._lock:
            q = self._queues.get(device_id, [])
            return list(q[:limit])

    def ack_command(self, device_id: str, command_id: str, ok: bool = True) -> bool:
        """Remove command from pending queue upon ESP32 acknowledgment."""
        with self._lock:
            q = self._queues.get(device_id, [])
            found = False
            remaining = []
            for item in q:
                if item.get("id") == command_id:
                    found = True
                    self._acked_commands[command_id] = {
                        "device_id": device_id,
                        "acked_at": time.time(),
                        "ok": ok,
                    }
                else:
                    remaining.append(item)
            self._queues[device_id] = remaining
            if found:
                logger.info("Acknowledged command [%s] for device [%s]", command_id, device_id)
            return found

    def clear_device_queue(self, device_id: str):
        with self._lock:
            self._queues.pop(device_id, None)

    @staticmethod
    def _resolve_cmd_string(channel: str, is_on: bool, action: str) -> str:
        suffix = "on" if is_on else "off"

        # Semua saklar (Lampu + Relay)
        if channel in ("all", "semua", "seluruh", "semua_perangkat"):
            return "on" if is_on else "off"

        # Semua Lampu
        if channel in ("lamp", "all_lights", "semua_lampu", "lampu_semua"):
            return f"lamp_{suffix}"

        # Lampu Tengah (GPIO 21)
        if "tengah" in channel:
            return f"lamp_tengah_{suffix}"

        # Lampu Dapur / Tamu (GPIO 17)
        if "dapur" in channel or "tamu" in channel:
            return f"lamp_dapur_tamu_{suffix}"

        # Lampu Kamar (GPIO 16)
        if "kamar" in channel:
            return f"lamp_kamar_{suffix}"

        # Relay / Kipas Exhaust (GPIO 32)
        if "relay" in channel or "fan" in channel or "kipas" in channel:
            return f"relay_{suffix}"

        # Buzzer (GPIO 19)
        if "buzzer" in channel or "sirine" in channel or "alarm" in channel:
            return f"buzzer_{suffix}"

        # Fallback format: {channel}_{suffix}
        return f"{channel}_{suffix}"


# Singleton instance
device_queue = DeviceCommandQueue()
