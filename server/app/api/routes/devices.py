import datetime
import json
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from server.app.api.deps import get_current_user, record_audit_log, require_role
from server.app.core.database import get_db
from server.app.core.mqtt_auth import (
    generate_device_mqtt_credentials,
    revoke_device_mqtt_credentials,
)
from server.app.core.mqtt_client import mqtt_service
from server.app.core.ws_manager import ws_manager
from server.app.models.automation import Automation, NotificationLog
from server.app.models.device import Channel, Device, TelemetryLog
from server.app.models.user import User

router = APIRouter(tags=["devices"])


# --- Schemas ---
class ChannelInput(BaseModel):
    channel_key: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=100)
    channel_type: Literal["switch", "relay", "gas_sensor", "light_sensor", "buzzer"]
    unit: Optional[str] = None


class CreateDeviceRequest(BaseModel):
    id: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_\-]+$")
    name: str = Field(..., min_length=2, max_length=100)
    room: str = Field("Umum", max_length=50)
    device_type: str = Field("esp32", max_length=30)
    channels: Optional[List[ChannelInput]] = None


class CommandRequest(BaseModel):
    channel: str = Field(..., description="channel_key yang dituju")
    action: str = Field("set", description="Aksi: set, toggle, pulse")
    value: Any = Field(..., description="Nilai baru: true/false/int")


class CreateAutomationRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    trigger_type: str = Field("sensor_threshold")
    trigger_config: Dict[str, Any]
    action_config: Dict[str, Any]
    is_enabled: bool = True


# --- Endpoints Perangkat ---

@router.get("/devices")
async def list_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ambil daftar semua perangkat beserta kanalnya."""
    query = select(Device).options(selectinload(Device.channels)).order_by(Device.created_at.desc())
    result = await db.execute(query)
    devices = result.scalars().all()

    items = []
    for d in devices:
        items.append({
            "id": d.id,
            "name": d.name,
            "room": d.room,
            "device_type": d.device_type,
            "is_online": d.is_online,
            "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
            "ip_address": d.ip_address,
            "mqtt_username": d.mqtt_username,
            "channels": [
                {
                    "id": c.id,
                    "channel_key": c.channel_key,
                    "name": c.name,
                    "channel_type": c.channel_type,
                    "current_value": c.current_value,
                    "unit": c.unit,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                }
                for c in d.channels
            ],
        })
    return {"status": "ok", "devices": items}


@router.post("/devices", status_code=status.HTTP_201_CREATED)
async def create_device(
    payload: CreateDeviceRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    """Tambah perangkat baru dan buat kredensial MQTT unik (Hanya Admin)."""
    # Cek ID unik
    existing = await db.execute(select(Device).where(Device.id == payload.id))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Perangkat dengan ID '{payload.id}' sudah terdaftar.",
        )

    # 1. Buat kredensial MQTT acak dan update ACL Mosquitto
    creds = generate_device_mqtt_credentials(payload.id)

    # 2. Simpan perangkat ke DB
    dev = Device(
        id=payload.id,
        name=payload.name,
        room=payload.room,
        device_type=payload.device_type,
        is_online=False,
        mqtt_username=creds["mqtt_username"],
        mqtt_password_hash=creds["mqtt_password"],  # disimpan untuk referensi
    )
    db.add(dev)

    # 3. Tambahkan kanal awal
    channels_to_add = payload.channels or [
        ChannelInput(channel_key="lamp_tengah", name="Lampu Tengah", channel_type="switch"),
        ChannelInput(channel_key="lamp_dapur_tamu", name="Lampu Dapur & Tamu", channel_type="switch"),
        ChannelInput(channel_key="lamp_kamar", name="Lampu Kamar", channel_type="switch"),
        ChannelInput(channel_key="relay_fan", name="Kipas Exhaust", channel_type="relay"),
        ChannelInput(channel_key="buzzer", name="Sirine Alarm", channel_type="buzzer"),
        ChannelInput(channel_key="mq2", name="Sensor Gas MQ-2", channel_type="gas_sensor", unit="raw"),
        ChannelInput(channel_key="ldr", name="Sensor Cahaya LDR", channel_type="light_sensor", unit="digital"),
    ]

    for ch in channels_to_add:
        c_obj = Channel(
            device_id=payload.id,
            channel_key=ch.channel_key,
            name=ch.name,
            channel_type=ch.channel_type,
            unit=ch.unit,
            current_value="false" if ch.channel_type in {"switch", "relay", "buzzer"} else "0",
        )
        db.add(c_obj)

    await db.commit()

    # Catat audit log
    client_ip = request.client.host if request.client else "127.0.0.1"
    await record_audit_log(
        db=db,
        action="device.create",
        user_id=admin.id,
        username=admin.username,
        target_type="device",
        target_id=payload.id,
        details={"name": payload.name, "room": payload.room},
        ip_address=client_ip,
    )

    # Kembalikan kredensial MQTT SEKALI SAJA ke UI admin
    return {
        "status": "ok",
        "message": "Perangkat berhasil didaftarkan.",
        "device": {
            "id": dev.id,
            "name": dev.name,
            "room": dev.room,
            "device_type": dev.device_type,
        },
        "mqtt_credentials": {
            "broker_host": "127.0.0.1",
            "broker_port": 1883,
            "topic_prefix": f"home/{dev.id}",
            "client_id": dev.id,
            "username": creds["mqtt_username"],
            "password": creds["mqtt_password"],
        },
    }


@router.delete("/devices/{device_id}")
async def delete_device(
    device_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    """Hapus perangkat dan cabut kredensial MQTT (Hanya Admin)."""
    res = await db.execute(select(Device).where(Device.id == device_id))
    dev = res.scalar_one_or_none()
    if not dev:
        raise HTTPException(status_code=404, detail="Perangkat tidak ditemukan.")

    revoke_device_mqtt_credentials(device_id)
    await db.delete(dev)
    await db.commit()

    client_ip = request.client.host if request.client else "127.0.0.1"
    await record_audit_log(
        db=db,
        action="device.delete",
        user_id=admin.id,
        username=admin.username,
        target_type="device",
        target_id=device_id,
        details={"name": dev.name},
        ip_address=client_ip,
    )

    return {"status": "ok", "message": f"Perangkat '{device_id}' berhasil dihapus."}


@router.post("/devices/{device_id}/revoke-credentials")
async def revoke_credentials(
    device_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    """Buat ulang kredensial MQTT baru untuk perangkat (Hanya Admin)."""
    res = await db.execute(select(Device).where(Device.id == device_id))
    dev = res.scalar_one_or_none()
    if not dev:
        raise HTTPException(status_code=404, detail="Perangkat tidak ditemukan.")

    creds = generate_device_mqtt_credentials(device_id)
    dev.mqtt_password_hash = creds["mqtt_password"]
    await db.commit()

    client_ip = request.client.host if request.client else "127.0.0.1"
    await record_audit_log(
        db=db,
        action="device.rotate_credentials",
        user_id=admin.id,
        username=admin.username,
        target_type="device",
        target_id=device_id,
        details={},
        ip_address=client_ip,
    )

    return {
        "status": "ok",
        "message": "Kredensial MQTT berhasil diperbarui.",
        "mqtt_credentials": {
            "username": creds["mqtt_username"],
            "password": creds["mqtt_password"],
        },
    }


@router.post("/devices/{device_id}/cmd")
async def send_device_command(
    device_id: str,
    payload: CommandRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Kirim perintah kontrol ke kanal perangkat via MQTT (Admin & Member)."""
    # Child tidak diizinkan mengubah saklar utama jika dibatasi
    if current_user.role == "child":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Peran anak (child) tidak memiliki izin mengontrol perangkat ini.",
        )

    # Validasi kanal
    q = select(Channel).where(Channel.device_id == device_id, Channel.channel_key == payload.channel)
    r = await db.execute(q)
    ch = r.scalar_one_or_none()
    if not ch:
        raise HTTPException(status_code=404, detail="Kanal tidak ditemukan pada perangkat ini.")

    cmd_id = f"cmd_{int(datetime.datetime.utcnow().timestamp() * 1000)}"
    cmd_payload = {
        "id": cmd_id,
        "channel": payload.channel,
        "action": payload.action,
        "value": payload.value,
    }

    # Kirim ke MQTT
    published = mqtt_service.publish_command(device_id, cmd_payload)

    # Update optimis di DB lokal
    val_str = str(payload.value).lower() if isinstance(payload.value, bool) else str(payload.value)
    ch.current_value = val_str
    await db.commit()

    # Siarkan ke WebSocket
    await ws_manager.broadcast({
        "type": "state",
        "device_id": device_id,
        "channels": {payload.channel: payload.value},
        "timestamp": datetime.datetime.utcnow().isoformat(),
    })

    client_ip = request.client.host if request.client else "127.0.0.1"
    await record_audit_log(
        db=db,
        action="device.cmd",
        user_id=current_user.id,
        username=current_user.username,
        target_type="channel",
        target_id=f"{device_id}:{payload.channel}",
        details={"action": payload.action, "value": payload.value, "published": published},
        ip_address=client_ip,
    )

    return {
        "status": "ok",
        "cmd_id": cmd_id,
        "published_to_mqtt": published,
        "current_value": val_str,
    }


@router.get("/devices/{device_id}/telemetry")
async def get_telemetry_history(
    device_id: str,
    channel_key: Optional[str] = Query(None, description="Kanal sensor: mq2, ldr, dll"),
    limit: int = Query(50, ge=5, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ambil riwayat data telemetri sensor untuk grafik."""
    q = select(TelemetryLog).where(TelemetryLog.device_id == device_id)
    if channel_key:
        q = q.where(TelemetryLog.channel_key == channel_key)
    q = q.order_by(desc(TelemetryLog.created_at)).limit(limit)

    res = await db.execute(q)
    rows = res.scalars().all()

    # Kembalikan urutan kronologis untuk grafik
    items = [
        {
            "id": r.id,
            "channel_key": r.channel_key,
            "value": r.value_num,
            "created_at": r.created_at.isoformat(),
        }
        for r in reversed(rows)
    ]

    return {"status": "ok", "device_id": device_id, "telemetry": items}


# --- Endpoints Otomasi ---

@router.get("/automations")
async def list_automations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ambil semua daftar aturan otomasi."""
    q = select(Automation).order_by(Automation.created_at.desc())
    res = await db.execute(q)
    rows = res.scalars().all()

    items = []
    for a in rows:
        items.append({
            "id": a.id,
            "name": a.name,
            "is_enabled": a.is_enabled,
            "trigger_type": a.trigger_type,
            "trigger_config": json.loads(a.trigger_config) if a.trigger_config else {},
            "action_config": json.loads(a.action_config) if a.action_config else {},
            "created_at": a.created_at.isoformat(),
        })
    return {"status": "ok", "automations": items}


@router.post("/automations", status_code=status.HTTP_201_CREATED)
async def create_automation(
    payload: CreateAutomationRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    """Buat aturan otomasi baru (Hanya Admin)."""
    auto = Automation(
        name=payload.name,
        is_enabled=payload.is_enabled,
        trigger_type=payload.trigger_type,
        trigger_config=json.dumps(payload.trigger_config),
        action_config=json.dumps(payload.action_config),
    )
    db.add(auto)
    await db.commit()
    await db.refresh(auto)
    return {"status": "ok", "id": auto.id, "name": auto.name}


@router.delete("/automations/{automation_id}")
async def delete_automation(
    automation_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    """Hapus aturan otomasi (Hanya Admin)."""
    q = select(Automation).where(Automation.id == automation_id)
    r = await db.execute(q)
    item = r.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Otomasi tidak ditemukan.")

    await db.delete(item)
    await db.commit()
    return {"status": "ok", "message": f"Otomasi {automation_id} dihapus."}


# --- Endpoints Notifikasi ---

@router.get("/notifications")
async def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ambil daftar kejadian dan peringatan darurat."""
    q = select(NotificationLog).order_by(desc(NotificationLog.created_at)).limit(limit)
    res = await db.execute(q)
    rows = res.scalars().all()

    items = [
        {
            "id": n.id,
            "device_id": n.device_id,
            "event_type": n.event_type,
            "message": n.message,
            "severity": n.severity,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
        }
        for n in rows
    ]
    return {"status": "ok", "notifications": items}


# --- WebSocket Endpoint ---

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Kanal WebSocket untuk pembaruan status realtime di aplikasi Flutter."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Terima ping / pesan dari klien
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)
