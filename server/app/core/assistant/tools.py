import datetime
import json
import logging
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.core.assistant.item_search import execute_find_item
from server.app.core.device_queue import device_queue
from server.app.core.mqtt_client import mqtt_service
from server.app.core.ws_manager import ws_manager
from server.app.models.assistant import PendingConfirmation
from server.app.models.audit import AuditLog
from server.app.models.device import Channel, Device
from server.app.models.family import FamilyDailySummary, FamilySettings
from server.app.models.user import User

logger = logging.getLogger("server.assistant.tools")

# Schema definisi alat untuk LLM (format OpenAI/DeepSeek Tool Calling)
ASSISTANT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "control_device",
            "description": "Mengontrol perangkat atau kanal tertentu (menyalakan/mematikan lampu, saklar, atau kipas).",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Nama panggilan (alias) atau nama kanal perangkat, misalnya 'lampu kamar', 'kipas', atau 'lamp_tengah'.",
                    },
                    "action": {
                        "type": "string",
                        "enum": ["turn_on", "turn_off", "toggle"],
                        "description": "Aksi yang diinginkan: 'turn_on' (nyalakan), 'turn_off' (matikan), atau 'toggle'.",
                    },
                },
                "required": ["channel", "action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_device_states",
            "description": "Mendapatkan status terkini dari semua kanal perangkat (lampu, relay, saklar) di rumah.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sensor_readings",
            "description": "Mendapatkan data pembacaan sensor aktif (seperti sensor gas MQ-2, sensor cahaya LDR, dll).",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_item",
            "description": "Mencari lokasi barang atau benda di rumah.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Nama barang yang dicari.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_family_summary",
            "description": "Mendapatkan ringkasan aktivitas anggota keluarga.",
            "parameters": {
                "type": "object",
                "properties": {
                    "range": {
                        "type": "string",
                        "enum": ["hari_ini", "minggu_ini"],
                        "description": "Rentang waktu ringkasan.",
                    },
                },
                "required": ["range"],
            },
        },
    },
]


class AssistantToolExecutor:
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user

    async def find_channel(self, identifier: str) -> Optional[Channel]:
        clean_id = identifier.strip().lower()
        stmt = select(Channel)
        result = await self.db.execute(stmt)
        channels = result.scalars().all()

        # 1. Exact match pada alias, name, atau channel_key
        for ch in channels:
            if ch.alias and ch.alias.lower() == clean_id:
                return ch
            if ch.name.lower() == clean_id:
                return ch
            if ch.channel_key.lower() == clean_id:
                return ch

        # 2. Fuzzy/Substring match
        for ch in channels:
            if ch.alias and (clean_id in ch.alias.lower() or ch.alias.lower() in clean_id):
                return ch
            if clean_id in ch.name.lower() or ch.name.lower() in clean_id:
                return ch

        return None

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mengeksekusi alat dengan verifikasi identitas, peran pengguna, dan pencatatan audit log.
        """
        logger.info(f"User '{self.user.username}' ({self.user.role}) memicu alat '{name}' dengan argumen: {arguments}")

        # Catat rencana pemanggilan alat di audit log
        audit = AuditLog(
            user_id=self.user.id,
            action=f"assistant.tool.{name}",
            target_type="assistant",
            target_id=name,
            details=json.dumps({"arguments": arguments, "role": self.user.role}),
        )
        self.db.add(audit)
        await self.db.commit()

        if name == "find_item":
            query = arguments.get("query", "")
            return await execute_find_item(self.db, self.user, query)

        if name == "get_family_summary":
            if self.user.role != "admin":
                return {"error": "Akses ditolak: Hanya admin yang dapat mengakses ringkasan keluarga."}

            stmt_cfg = select(FamilySettings).where(FamilySettings.id == "default")
            fam_cfg = (await self.db.execute(stmt_cfg)).scalar_one_or_none()

            # Saklar admin default MATI: jika belum ada atau allow_assistant_family_summary False -> tolak jujur
            if not fam_cfg or not fam_cfg.allow_assistant_family_summary:
                return {
                    "status": "disabled",
                    "result": "dinonaktifkan",
                    "message": "Fitur ringkasan keluarga untuk asisten dinonaktifkan oleh administrator.",
                }

            # Saklar aktif: ambil angka agregat tanpa nama dan tanpa jam per orang
            today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
            stmt_sum = select(FamilyDailySummary).where(FamilyDailySummary.date == today_str)
            summary = (await self.db.execute(stmt_sum)).scalar_one_or_none()

            if not summary:
                return {
                    "status": "success",
                    "result": f"Belum ada data agregat aktivitas keluarga untuk tanggal {today_str}.",
                    "study_minutes": 0,
                    "late_night_count": 0,
                    "fall_incident_count": 0,
                    "inactivity_count": 0,
                    "hazard_alert_count": 0,
                }

            return {
                "status": "success",
                "result": summary.summary_text,
                "study_minutes": summary.study_minutes,
                "late_night_count": summary.late_night_count,
                "fall_incident_count": summary.fall_incident_count,
                "inactivity_count": summary.inactivity_count,
                "hazard_alert_count": summary.hazard_alert_count,
            }

        if name == "get_device_states":
            stmt = select(Channel)
            res = await self.db.execute(stmt)
            channels = res.scalars().all()
            # Hanya kembalikan status perangkat (tidak ada data kamera atau privasi)
            output = []
            for ch in channels:
                output.append({
                    "id": ch.id,
                    "name": ch.name,
                    "alias": ch.alias,
                    "type": ch.channel_type,
                    "state": ch.current_value or "unknown",
                    "is_sensitive": ch.is_sensitive,
                })
            return {"devices": output}

        if name == "get_sensor_readings":
            stmt = select(Channel).where(Channel.channel_type.in_(["gas_sensor", "light_sensor", "sensor"]))
            res = await self.db.execute(stmt)
            sensors = res.scalars().all()
            output = []
            for s in sensors:
                output.append({
                    "name": s.name,
                    "alias": s.alias,
                    "value": s.current_value or "0",
                    "unit": s.unit or "",
                })
            return {"sensors": output}

        if name == "control_device":
            target = arguments.get("channel", "")
            action = arguments.get("action", "")

            # Tangani aksi massal: all_on atau all_off
            if target.lower() in ["semua", "all", "seluruhnya", "semua lampu"] or action in ["all_on", "all_off"]:
                if self.user.role == "child":
                    return {"error": "Akses ditolak: Akun anak tidak dapat memicu aksi massal seluruh perangkat."}
                
                # Aksi massal WAJIB konfirmasi!
                conf_id = str(uuid.uuid4())
                pending = PendingConfirmation(
                    id=conf_id,
                    user_id=self.user.id,
                    channel_id=None,
                    channel_name="Semua Perangkat",
                    action=action if action in ["all_on", "all_off"] else ("all_on" if action == "turn_on" else "all_off"),
                    description=f"Konfirmasi mematikan/menyalakan semua perangkat secara serentak.",
                    expires_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
                )
                self.db.add(pending)
                await self.db.commit()

                return {
                    "status": "pending_confirmation",
                    "confirmation_id": conf_id,
                    "channel_name": "Semua Perangkat",
                    "action": pending.action,
                    "message": "Aksi mematikan/menyalakan semua perangkat memerlukan konfirmasi eksplisit.",
                }

            ch = await self.find_channel(target)
            if not ch:
                return {"error": f"Kanal perangkat dengan nama atau alias '{target}' tidak ditemukan."}

            # Cek izin peran akun anak
            if self.user.role == "child":
                if ch.is_sensitive:
                    return {"error": f"Akses ditolak: Kanal '{ch.name}' ditandai sensitif dan tidak dapat dikontrol oleh akun anak."}
                if not ch.allowed_for_child:
                    return {"error": f"Akses ditolak: Akun anak tidak memiliki izin untuk mengontrol kanal '{ch.name}'."}


            # Cek jika kanal sensitif -> butuh konfirmasi
            if ch.is_sensitive:
                conf_id = str(uuid.uuid4())
                pending = PendingConfirmation(
                    id=conf_id,
                    user_id=self.user.id,
                    channel_id=ch.id,
                    device_id=ch.device_id,
                    channel_key=ch.channel_key,
                    channel_name=ch.name,
                    action=action,
                    description=f"Kanal '{ch.name}' adalah kanal sensitif. Apakah Anda yakin ingin melakukan {action}?",
                    expires_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
                )
                self.db.add(pending)
                await self.db.commit()

                return {
                    "status": "pending_confirmation",
                    "confirmation_id": conf_id,
                    "channel_name": ch.name,
                    "action": action,
                    "message": f"Kanal '{ch.name}' ditandai sensitif. Perlu konfirmasi pengguna sebelum dieksekusi.",
                }

            # Eksekusi aksi kontrol non-sensitif
            val_bool = True if action == "turn_on" else (False if action == "turn_off" else (ch.current_value != "true"))
            ch.current_value = "true" if val_bool else "false"
            ch.updated_at = datetime.datetime.utcnow()

            # Publikasikan perintah ke antrean polling HTTP ESP32 dan MQTT broker
            device_cmd_payload = {
                "id": str(uuid.uuid4()),
                "channel": ch.channel_key,
                "action": "set",
                "value": val_bool,
            }
            device_queue.enqueue_command(ch.device_id, device_cmd_payload)
            mqtt_service.publish_command(ch.device_id, device_cmd_payload)
            await ws_manager.broadcast({
                "type": "state",
                "device_id": ch.device_id,
                "channels": {ch.channel_key: val_bool},
                "timestamp": datetime.datetime.utcnow().isoformat(),
            })
            await self.db.commit()

            status_str = "dinyalakan" if val_bool else "dimatikan"
            return {
                "status": "success",
                "channel_id": ch.id,
                "channel_name": ch.name,
                "current_value": ch.current_value,
                "message": f"{ch.name} berhasil {status_str}.",
            }

        return {"error": f"Alat '{name}' tidak dikenali oleh sistem."}
