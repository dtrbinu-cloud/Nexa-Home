"""
Layanan Retensi Otomatis Klip Rekaman Kamera (Tahap 4).
- Menghapus rekaman yang lebih tua dari batas retensi hari (default 7 hari).
- Menjaga total pemakaian disk rekaman di bawah kuota (hapus terlama lebih dulu).
- Mengecek sisa ruang penyimpanan: menghentikan rekaman jika disk < ambang batas (default 500 MB).
"""

from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path
from typing import Tuple

import psutil
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.core.config import settings
from server.app.core.database import async_session_factory
from server.app.models.camera import MotionClip

logger = logging.getLogger("server.camera.retention")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def check_disk_space_available() -> Tuple[bool, float]:
    """
    Mengecek apakah sisa ruang disk mencukupi untuk melanjutkan perekaman.
    Returns: (is_safe_to_record, free_mb)
    """
    storage_path = Path(settings.RECORDING_STORAGE_DIR)
    storage_path.mkdir(parents=True, exist_ok=True)

    try:
        usage = psutil.disk_usage(str(storage_path))
        free_mb = usage.free / (1024 * 1024)
        is_safe = free_mb >= settings.RECORDING_MIN_FREE_DISK_MB
        if not is_safe:
            logger.warning(
                f"[Disk Space Warning] Sisa ruang disk tersisa {free_mb:.1f} MB, "
                f"di bawah ambang batas aman {settings.RECORDING_MIN_FREE_DISK_MB} MB. Perekaman dijeda."
            )
        return is_safe, free_mb
    except Exception as e:
        logger.error(f"Gagal memeriksa ruang disk: {e}")
        return True, 9999.0


async def cleanup_expired_clips(db: AsyncSession) -> int:
    """Menghapus klip yang lebih tua dari batas retensi hari."""
    retention_days = settings.RECORDING_RETENTION_DAYS
    cutoff_time = utcnow() - timedelta(days=retention_days)

    stmt = select(MotionClip).where(MotionClip.created_at < cutoff_time)
    result = await db.execute(stmt)
    expired_clips = result.scalars().all()

    deleted_count = 0
    for clip in expired_clips:
        # Hapus file fisik di disk
        _delete_clip_files(clip)
        await db.delete(clip)
        deleted_count += 1

    if deleted_count > 0:
        await db.commit()
        logger.info(f"[Retensi] {deleted_count} klip rekaman kedaluwarsa (> {retention_days} hari) berhasil dihapus.")

    return deleted_count


async def enforce_max_storage_quota(db: AsyncSession) -> int:
    """Menghapus klip tertua jika total ukuran rekaman melebihi batas RECORDING_MAX_DISK_MB."""
    max_bytes = settings.RECORDING_MAX_DISK_MB * 1024 * 1024

    stmt = select(func.coalesce(func.sum(MotionClip.file_size_bytes), 0))
    total_bytes = (await db.execute(stmt)).scalar_one()

    deleted_count = 0
    if total_bytes > max_bytes:
        logger.info(
            f"[Kapasitas Disk] Total ukuran rekaman ({total_bytes / (1024*1024):.1f} MB) "
            f"melebihi batas kuota {settings.RECORDING_MAX_DISK_MB} MB. Menghapus klip tertua..."
        )

        # Ambil klip dari yang paling tua
        clips_stmt = select(MotionClip).order_by(MotionClip.created_at.asc())
        clips = (await db.execute(clips_stmt)).scalars().all()

        current_bytes = total_bytes
        for clip in clips:
            if current_bytes <= max_bytes:
                break
            _delete_clip_files(clip)
            current_bytes -= clip.file_size_bytes
            await db.delete(clip)
            deleted_count += 1

        await db.commit()
        logger.info(f"[Kapasitas Disk] {deleted_count} klip tertua dihapus untuk mematuhi kuota.")

    return deleted_count


def _delete_clip_files(clip: MotionClip):
    """Menghapus file rekaman terenkripsi dan berkas thumbnail dari filesystem."""
    try:
        if clip.file_path:
            p = Path(clip.file_path)
            if p.exists():
                p.unlink()
        if clip.thumbnail_path:
            t = Path(clip.thumbnail_path)
            if t.exists():
                t.unlink()
    except Exception as e:
        logger.warning(f"Gagal menghapus file klip {clip.id}: {e}")


async def run_retention_maintenance() -> dict:
    """Menjalankan seluruh siklus pemeliharaan retensi klip rekaman."""
    async with async_session_factory() as db:
        is_safe, free_mb = check_disk_space_available()
        expired_deleted = await cleanup_expired_clips(db)
        quota_deleted = await enforce_max_storage_quota(db)

        return {
            "is_disk_safe": is_safe,
            "free_disk_mb": free_mb,
            "expired_clips_deleted": expired_deleted,
            "quota_clips_deleted": quota_deleted,
        }
