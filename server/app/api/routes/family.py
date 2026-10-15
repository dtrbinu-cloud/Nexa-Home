"""
Router API Analitik Keluarga (Tahap 6 - Admin Saja).
- Akses data analitik keluarga hanya untuk admin (member & child ditolak 403 Forbidden).
- Endpoint transparansi 'Apa yang dipantau' (/transparency) terbuka untuk semua peran.
- Setiap akses ke data keluarga dicatat di audit log.
- Tombol 'Hapus semua data keluarga' dengan konfirmasi menghapus seluruh log & ringkasan.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.api.deps import get_current_user, record_audit_log, require_role
from server.app.core.config import settings
from server.app.core.database import get_db
from server.app.core.family.rules_engine import generate_local_family_summary
from server.app.models.camera import AIWorkerHeartbeat, Camera
from server.app.models.family import (
    CameraZone,
    FamilyDailySummary,
    FamilyEventLog,
    FamilySettings,
)
from server.app.models.user import User

logger = logging.getLogger("server.family.api")

router = APIRouter(prefix="/family", tags=["Family Analytics"])


# --- Schemas ---
class ZoneCreateRequest(BaseModel):
    camera_id: str
    name: str = Field(..., min_length=1, max_length=100)
    zone_type: str = Field(..., pattern="^(belajar|umum|berbahaya)$")
    polygon: List[List[float]]  # [[x, y], ...]


class ZoneUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    zone_type: Optional[str] = Field(None, pattern="^(belajar|umum|berbahaya)$")
    polygon: Optional[List[List[float]]] = None


class FamilySettingsUpdateRequest(BaseModel):
    enabled: Optional[bool] = None
    study_zone_enabled: Optional[bool] = None
    study_gap_tolerance_minutes: Optional[int] = Field(None, ge=1, le=60)
    late_night_enabled: Optional[bool] = None
    late_night_start: Optional[str] = None
    late_night_end: Optional[str] = None
    late_night_min_minutes: Optional[int] = Field(None, ge=1, le=120)
    fall_detection_enabled: Optional[bool] = None
    fall_stationary_seconds: Optional[int] = Field(None, ge=5, le=300)
    inactivity_enabled: Optional[bool] = None
    inactivity_min_minutes: Optional[int] = Field(None, ge=10, le=720)
    hazard_zone_enabled: Optional[bool] = None
    allow_assistant_family_summary: Optional[bool] = None
    stats_retention_days: Optional[int] = Field(None, ge=7, le=365)
    events_retention_days: Optional[int] = Field(None, ge=1, le=180)


# =============================================================================
# 1. TRANSPARANSI "APA YANG DIPANTAU" (Terbuka untuk SEMUA akun tanpa data sensitif)
# =============================================================================
@router.get("/transparency")
async def get_monitoring_transparency(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Halaman transparansi 'Apa yang dipantau' yang bisa dibuka oleh semua akun:
    Daftar fitur yang aktif dan kamera yang dipakai, TANPA data metrik keluarga.
    """
    stmt_cfg = select(FamilySettings).where(FamilySettings.id == "default")
    fam_cfg = (await db.execute(stmt_cfg)).scalar_one_or_none()

    stmt_cams = select(Camera).where(Camera.status == "online", Camera.privacy_mode == False)
    cameras = (await db.execute(stmt_cams)).scalars().all()

    stmt_zones = select(CameraZone)
    zones = (await db.execute(stmt_zones)).scalars().all()

    # Periksa status worker AI (ketahanan: jika heartbeat stale > 15s -> worker offline)
    stmt_hb = select(AIWorkerHeartbeat).where(AIWorkerHeartbeat.id == "vision_worker_1")
    hb = (await db.execute(stmt_hb)).scalar_one_or_none()

    worker_online = False
    if hb and hb.last_heartbeat:
        last_hb = hb.last_heartbeat.replace(tzinfo=timezone.utc) if hb.last_heartbeat.tzinfo is None else hb.last_heartbeat
        time_diff = (datetime.now(timezone.utc) - last_hb).total_seconds()
        worker_online = time_diff <= settings.VISION_HEARTBEAT_TIMEOUT_SECONDS

    features_status = {
        "master_enabled": fam_cfg.enabled if fam_cfg else False,
        "study_zone_monitoring": fam_cfg.study_zone_enabled if fam_cfg else False,
        "late_night_activity_monitoring": fam_cfg.late_night_enabled if fam_cfg else False,
        "fall_detection_monitoring": fam_cfg.fall_detection_enabled if fam_cfg else False,
        "inactivity_monitoring": fam_cfg.inactivity_enabled if fam_cfg else False,
        "hazard_zone_monitoring": fam_cfg.hazard_zone_enabled if fam_cfg else False,
        "assistant_integration": fam_cfg.allow_assistant_family_summary if fam_cfg else False,
    }

    camera_list = [
        {"id": c.id, "name": c.name, "room_id": c.room_id or "default"}
        for c in cameras
    ]

    zone_list = [
        {"id": z.id, "camera_id": z.camera_id, "name": z.name, "zone_type": z.zone_type}
        for z in zones
    ]

    return {
        "status": "success",
        "ai_worker_status": "online" if worker_online else "offline",
        "disclaimer": "Bukan alat medis. Hanya angka dan kejadian dari kamera ruang umum, tanpa menyimpan video dan tanpa pengenalan wajah.",
        "active_features": features_status,
        "monitored_cameras": camera_list,
        "monitored_zones": zone_list,
    }


# =============================================================================
# 2. KONFIGURASI DAN SAKLAR (Admin Saja)
# =============================================================================
@router.get("/settings")
async def get_family_settings(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Mengambil konfigurasi analitik keluarga dan saklar fitur."""
    await record_audit_log(
        db,
        action="family.settings.read",
        user_id=current_user.id,
        username=current_user.username,
        target_type="family_settings",
    )

    stmt = select(FamilySettings).where(FamilySettings.id == "default")
    fam_cfg = (await db.execute(stmt)).scalar_one_or_none()

    if not fam_cfg:
        fam_cfg = FamilySettings(id="default")
        db.add(fam_cfg)
        await db.commit()
        await db.refresh(fam_cfg)

    return {
        "status": "success",
        "settings": {
            "enabled": fam_cfg.enabled,
            "study_zone_enabled": fam_cfg.study_zone_enabled,
            "study_gap_tolerance_minutes": fam_cfg.study_gap_tolerance_minutes,
            "late_night_enabled": fam_cfg.late_night_enabled,
            "late_night_start": fam_cfg.late_night_start,
            "late_night_end": fam_cfg.late_night_end,
            "late_night_min_minutes": fam_cfg.late_night_min_minutes,
            "fall_detection_enabled": fam_cfg.fall_detection_enabled,
            "fall_stationary_seconds": fam_cfg.fall_stationary_seconds,
            "inactivity_enabled": fam_cfg.inactivity_enabled,
            "inactivity_min_minutes": fam_cfg.inactivity_min_minutes,
            "hazard_zone_enabled": fam_cfg.hazard_zone_enabled,
            "allow_assistant_family_summary": fam_cfg.allow_assistant_family_summary,
            "stats_retention_days": fam_cfg.stats_retention_days,
            "events_retention_days": fam_cfg.events_retention_days,
            "updated_at": fam_cfg.updated_at.isoformat() if fam_cfg.updated_at else None,
        },
    }


@router.put("/settings")
async def update_family_settings(
    req: FamilySettingsUpdateRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Memperbarui konfigurasi analitik keluarga dan saklar fitur."""
    stmt = select(FamilySettings).where(FamilySettings.id == "default")
    fam_cfg = (await db.execute(stmt)).scalar_one_or_none()

    if not fam_cfg:
        fam_cfg = FamilySettings(id="default")
        db.add(fam_cfg)

    updates = req.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(fam_cfg, k, v)

    fam_cfg.updated_at = datetime.now(timezone.utc)
    await db.commit()

    await record_audit_log(
        db,
        action="family.settings.update",
        user_id=current_user.id,
        username=current_user.username,
        target_type="family_settings",
        details=updates,
    )

    return {"status": "success", "message": "Pengaturan keluarga berhasil diperbarui."}


# =============================================================================
# 3. ZONA POLIGON (Admin Saja)
# =============================================================================
@router.get("/zones")
async def list_zones(
    camera_id: Optional[str] = None,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Mengambil daftar zona poligon kamera."""
    await record_audit_log(
        db,
        action="family.zones.read",
        user_id=current_user.id,
        username=current_user.username,
        target_type="camera_zones",
    )

    stmt = select(CameraZone)
    if camera_id:
        stmt = stmt.where(CameraZone.camera_id == camera_id)

    zones = (await db.execute(stmt)).scalars().all()
    results = []
    for z in zones:
        try:
            poly = json.loads(z.polygon_json)
        except Exception:
            poly = []
        results.append({
            "id": z.id,
            "camera_id": z.camera_id,
            "name": z.name,
            "zone_type": z.zone_type,
            "polygon": poly,
            "created_at": z.created_at.isoformat() if z.created_at else None,
        })

    return {"status": "success", "zones": results}


@router.post("/zones")
async def create_zone(
    req: ZoneCreateRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Menambahkan zona poligon baru untuk kamera."""
    cam = await db.get(Camera, req.camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Kamera tidak ditemukan.")

    new_zone = CameraZone(
        id=str(uuid.uuid4()),
        camera_id=req.camera_id,
        name=req.name,
        zone_type=req.zone_type,
        polygon_json=json.dumps(req.polygon),
    )
    db.add(new_zone)
    await db.commit()

    await record_audit_log(
        db,
        action="family.zones.create",
        user_id=current_user.id,
        username=current_user.username,
        target_type="camera_zone",
        target_id=new_zone.id,
        details={"camera_id": req.camera_id, "name": req.name, "zone_type": req.zone_type},
    )

    return {"status": "success", "id": new_zone.id, "message": f"Zona '{req.name}' berhasil dibuat."}


@router.put("/zones/{zone_id}")
async def update_zone(
    zone_id: str,
    req: ZoneUpdateRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Memperbarui zona poligon."""
    zone = await db.get(CameraZone, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zona tidak ditemukan.")

    if req.name is not None:
        zone.name = req.name
    if req.zone_type is not None:
        zone.zone_type = req.zone_type
    if req.polygon is not None:
        zone.polygon_json = json.dumps(req.polygon)

    zone.updated_at = datetime.now(timezone.utc)
    await db.commit()

    await record_audit_log(
        db,
        action="family.zones.update",
        user_id=current_user.id,
        username=current_user.username,
        target_type="camera_zone",
        target_id=zone_id,
    )

    return {"status": "success", "message": "Zona berhasil diperbarui."}


@router.delete("/zones/{zone_id}")
async def delete_zone(
    zone_id: str,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Menghapus zona poligon."""
    zone = await db.get(CameraZone, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zona tidak ditemukan.")

    await db.delete(zone)
    await db.commit()

    await record_audit_log(
        db,
        action="family.zones.delete",
        user_id=current_user.id,
        username=current_user.username,
        target_type="camera_zone",
        target_id=zone_id,
    )

    return {"status": "success", "message": "Zona berhasil dihapus."}


# =============================================================================
# 4. RINGKASAN DAN KEJADIAN KELUARGA (Admin Saja)
# =============================================================================
@router.get("/summary")
async def get_family_summary(
    range_type: str = Query("today", alias="range", pattern="^(today|week)$"),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Mengambil ringkasan aktivitas keluarga harian atau mingguan.
    Hanya angka agregat tanpa nama per orang.
    """
    await record_audit_log(
        db,
        action="family.summary.read",
        user_id=current_user.id,
        username=current_user.username,
        target_type="family_summary",
        details={"range": range_type},
    )

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Pastikan ringkasan hari ini dibuat jika belum ada
    stmt_today = select(FamilyDailySummary).where(FamilyDailySummary.date == today_str)
    summary_today = (await db.execute(stmt_today)).scalar_one_or_none()
    if not summary_today:
        summary_today = await generate_local_family_summary(today_str)

    if range_type == "today":
        return {
            "status": "success",
            "range": "today",
            "date": today_str,
            "data": {
                "study_minutes": summary_today.study_minutes,
                "late_night_count": summary_today.late_night_count,
                "fall_incident_count": summary_today.fall_incident_count,
                "inactivity_count": summary_today.inactivity_count,
                "hazard_alert_count": summary_today.hazard_alert_count,
                "summary_text": summary_today.summary_text,
            },
        }
    else:
        # 7 hari terakhir
        stmt_week = select(FamilyDailySummary).order_by(FamilyDailySummary.date.desc()).limit(7)
        past_summaries = (await db.execute(stmt_week)).scalars().all()
        items = [
            {
                "date": s.date,
                "study_minutes": s.study_minutes,
                "late_night_count": s.late_night_count,
                "fall_incident_count": s.fall_incident_count,
                "inactivity_count": s.inactivity_count,
                "hazard_alert_count": s.hazard_alert_count,
                "summary_text": s.summary_text,
            }
            for s in reversed(past_summaries)
        ]
        return {"status": "success", "range": "week", "history": items}


@router.get("/events")
async def list_family_events(
    event_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Mengambil riwayat kejadian peringatan keluarga (Admin Saja)."""
    await record_audit_log(
        db,
        action="family.events.read",
        user_id=current_user.id,
        username=current_user.username,
        target_type="family_events",
    )

    stmt = select(FamilyEventLog).order_by(FamilyEventLog.created_at.desc())
    if event_type:
        stmt = stmt.where(FamilyEventLog.event_type == event_type)
    stmt = stmt.limit(limit)

    logs = (await db.execute(stmt)).scalars().all()
    results = []
    for l in logs:
        try:
            meta = json.loads(l.metadata_json)
        except Exception:
            meta = {}
        results.append({
            "id": l.id,
            "event_type": l.event_type,
            "camera_id": l.camera_id,
            "room_id": l.room_id,
            "title": l.title,
            "description": l.description,
            "severity": l.severity,
            "metadata": meta,
            "is_reviewed": l.is_reviewed,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        })

    return {"status": "success", "events": results}


@router.put("/events/{event_id}/review")
async def mark_event_reviewed(
    event_id: str,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Menandai peringatan sudah dilihat / ditinjau oleh admin."""
    event = await db.get(FamilyEventLog, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Kejadian tidak ditemukan.")

    event.is_reviewed = True
    await db.commit()

    await record_audit_log(
        db,
        action="family.events.review",
        user_id=current_user.id,
        username=current_user.username,
        target_type="family_event",
        target_id=event_id,
    )

    return {"status": "success", "message": "Peringatan ditandai sudah dilihat."}


# =============================================================================
# 5. HAPUS SEMUA DATA KELUARGA (Admin Saja dengan Konfirmasi)
# =============================================================================
@router.delete("/data")
async def clear_all_family_data(
    confirm: bool = Query(False, description="Harus bernilai True untuk konfirmasi penghapusan permanen"),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Menghapus seluruh rekaman kejadian dan ringkasan statistik keluarga.
    Hanya dapat dijalankan oleh admin dengan konfirmasi eksplisit.
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Konfirmasi diperlukan: tambahkan parameter ?confirm=true untuk menghapus permanen.",
        )

    # 1. Hapus seluruh kejadian analitik keluarga
    stmt_del_events = delete(FamilyEventLog)
    await db.execute(stmt_del_events)

    # 2. Hapus seluruh ringkasan statistik harian
    stmt_del_summaries = delete(FamilyDailySummary)
    await db.execute(stmt_del_summaries)

    await db.commit()

    # Catat audit log dengan aksi kritis
    await record_audit_log(
        db,
        action="family.data.purge_all",
        user_id=current_user.id,
        username=current_user.username,
        target_type="family_data",
        details={"severity": "CRITICAL", "message": "Seluruh log analitik dan ringkasan keluarga telah dihapus permanen oleh admin."},
    )

    logger.warning(f"Admin {current_user.username} (ID {current_user.id}) telah menghapus seluruh data analitik keluarga.")
    return {"status": "success", "message": "Semua data kejadian dan ringkasan statistik keluarga berhasil dihapus permanen."}
