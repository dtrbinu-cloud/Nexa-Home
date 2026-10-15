import re
from typing import Any, Dict, Tuple

from server.app.core.assistant.tools import AssistantToolExecutor


class LocalCommandParser:
    def __init__(self, tool_executor: AssistantToolExecutor):
        self.executor = tool_executor

    async def parse_and_execute(self, prompt: str) -> Tuple[str, Dict[str, Any] | None]:
        """
        Mem-parse perintah secara lokal berbasis aturan/regex sederhana saat LLM offline.
        Mengembalikan tuple: (jawaban_teks, pending_confirmation_atau_data)
        """
        text = prompt.strip().lower()

        # 1. Matikan semua / Nyalakan semua
        if "matikan semua" in text or "padamkan semua" in text:
            res = await self.executor.execute_tool("control_device", {"channel": "semua", "action": "turn_off"})
            if res.get("status") == "pending_confirmation":
                return (
                    f"[Mode Terbatas] Aksi mematikan semua perangkat memerlukan konfirmasi Anda.",
                    res,
                )
            return f"[Mode Terbatas] {res.get('message', res.get('error', 'Perintah dijalankan'))}", None

        if "nyalakan semua" in text or "hidupkan semua" in text:
            res = await self.executor.execute_tool("control_device", {"channel": "semua", "action": "turn_on"})
            if res.get("status") == "pending_confirmation":
                return (
                    f"[Mode Terbatas] Aksi menyalakan semua perangkat memerlukan konfirmasi Anda.",
                    res,
                )
            return f"[Mode Terbatas] {res.get('message', res.get('error', 'Perintah dijalankan'))}", None

        # 2. Nyalakan / Hidupkan
        on_match = re.search(r"\b(nyalakan|hidupkan|aktifkan|buka)\s+(.+)", text)
        if on_match:
            target = on_match.group(2).strip()
            # Bersihkan imbuhan seperti "dong", "tolong", "sekarang"
            target = re.sub(r"\b(dong|tolong|sekarang|please)\b", "", target).strip()
            res = await self.executor.execute_tool("control_device", {"channel": target, "action": "turn_on"})
            if res.get("status") == "pending_confirmation":
                return (
                    f"[Mode Terbatas] {res.get('message')}",
                    res,
                )
            if "error" in res:
                return f"[Mode Terbatas] {res['error']}", None
            return f"[Mode Terbatas] {res.get('message', 'Perangkat berhasil dinyalakan.')}", None

        # 3. Matikan / Padamkan
        off_match = re.search(r"\b(matikan|padamkan|nonaktifkan|tutup)\s+(.+)", text)
        if off_match:
            target = off_match.group(2).strip()
            target = re.sub(r"\b(dong|tolong|sekarang|please)\b", "", target).strip()
            res = await self.executor.execute_tool("control_device", {"channel": target, "action": "turn_off"})
            if res.get("status") == "pending_confirmation":
                return (
                    f"[Mode Terbatas] {res.get('message')}",
                    res,
                )
            if "error" in res:
                return f"[Mode Terbatas] {res['error']}", None
            return f"[Mode Terbatas] {res.get('message', 'Perangkat berhasil dimatikan.')}", None

        # 4. Status Sensor
        if any(kw in text for kw in ["sensor", "gas", "cahaya", "ldr", "mq2"]):
            res = await self.executor.execute_tool("get_sensor_readings", {})
            sensors = res.get("sensors", [])
            if not sensors:
                return "[Mode Terbatas] Tidak ada data sensor yang tersedia saat ini.", None
            lines = ["[Mode Terbatas] Pembacaan sensor terkini:"]
            for s in sensors:
                lines.append(f"- {s['name']}: {s['value']} {s['unit']}".strip())
            return "\n".join(lines), None

        # 5. Status Perangkat
        if any(kw in text for kw in ["status", "keadaan", "kondisi", "cek perangkat", "cek lampu"]):
            res = await self.executor.execute_tool("get_device_states", {})
            devices = res.get("devices", [])
            if not devices:
                return "[Mode Terbatas] Belum ada perangkat yang terdaftar di sistem.", None
            lines = ["[Mode Terbatas] Status perangkat:"]
            for d in devices:
                st = "Nyala" if d["state"] == "true" else ("Mati" if d["state"] == "false" else d["state"])
                alias_str = f" ({d['alias']})" if d.get("alias") else ""
                lines.append(f"- {d['name']}{alias_str}: {st}")
            return "\n".join(lines), None

        # 6. Pencarian Barang (find_item)
        find_match = re.search(r"\b(di mana|dimana|cari|temukan|lihat|posisi|keberadaan)\s+(.+)", text)
        if find_match:
            item_query = find_match.group(2).strip()
            item_query = re.sub(r"\b(dong|tolong|saya|ku|terakhir|sekarang|ya|ada)\b", "", item_query).strip()
            res = await self.executor.execute_tool("find_item", {"query": item_query})
            msg = res.get("message") or res.get("error") or res.get("result", "")
            return f"[Mode Terbatas] {msg}", res

        # 7. Perintah Tidak Dikenali
        return (
            "[Mode Terbatas] DeepSeek tidak dapat dijangkau. Dalam mode terbatas lokal, "
            "Anda dapat menyalakan/mematikan perangkat (misal 'nyalakan lampu'), mencari barang (misal 'di mana HP'), atau memeriksa 'status perangkat' / 'sensor'.",
            None,
        )
