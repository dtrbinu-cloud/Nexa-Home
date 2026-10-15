"""
Model Database untuk Kamera, Pairing, Klip Rekaman Gerakan, dan Izin Akses (Tahap 4).
"""

from datetime import datetime, timezone
import uuid
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    room_id: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="offline")  # online, offline, streaming

    # Privasi
    privacy_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    privacy_schedule: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON schedule

    # Audio (Default MATI untuk privasi)
    audio_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # AI Vision (Tahap 5)
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Pengaturan Deteksi & Retensi
    retention_days: Mapped[int] = mapped_column(Integer, default=7)
    motion_threshold: Mapped[int] = mapped_column(Integer, default=25)
    ignore_zones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list of zones

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    # Relasi
    tokens = relationship("CameraToken", back_populates="camera", cascade="all, delete-orphan")
    clips = relationship("MotionClip", back_populates="camera", cascade="all, delete-orphan")
    user_access = relationship("CameraUserAccess", back_populates="camera", cascade="all, delete-orphan")


class CameraToken(Base):
    __tablename__ = "camera_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    camera_id: Mapped[str] = mapped_column(String(64), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    camera = relationship("Camera", back_populates="tokens")


class CameraPairingCode(Base):
    __tablename__ = "camera_pairing_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    camera_name: Mapped[str] = mapped_column(String(100), nullable=False)
    room_id: Mapped[str] = mapped_column(String(50), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class MotionClip(Base):
    __tablename__ = "motion_clips"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id: Mapped[str] = mapped_column(String(64), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    # Path berkas terenkripsi di disk (AES-GCM)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    nonce: Mapped[str] = mapped_column(String(64), nullable=False)  # Hex nonce AES-GCM
    tag: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # Hex auth tag

    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    camera = relationship("Camera", back_populates="clips")


class CameraUserAccess(Base):
    """Hak akses spesifik akun member ke kamera tertentu."""
    __tablename__ = "camera_user_access"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    camera_id: Mapped[str] = mapped_column(String(64), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    camera = relationship("Camera", back_populates="user_access")


class DetectedItemLog(Base):
    """Log deteksi benda untuk fitur pencarian barang (Tahap 5)."""
    __tablename__ = "detected_item_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id: Mapped[str] = mapped_column(String(64), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    class_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    track_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Dedup & Timeline
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    # Posisi & Skor
    bbox_x: Mapped[float] = mapped_column(Float, default=0.0)
    bbox_y: Mapped[float] = mapped_column(Float, default=0.0)
    bbox_w: Mapped[float] = mapped_column(Float, default=0.0)
    bbox_h: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # Thumbnail Terenkripsi (AES-256-GCM)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(30), default="stream")  # "stream" atau "post_motion"

    camera = relationship("Camera")


class PersonPresenceEvent(Base):
    """Kejadian kehadiran orang anonim (Tahap 5). Tanpa gambar, tanpa identitas."""
    __tablename__ = "person_presence_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id: Mapped[str] = mapped_column(String(64), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    person_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    camera = relationship("Camera")


class AIWorkerHeartbeat(Base):
    """Pemantauan kesehatan Vision AI Worker (Tahap 5)."""
    __tablename__ = "ai_worker_heartbeats"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default="default_worker")
    status: Mapped[str] = mapped_column(String(30), default="online")
    last_heartbeat: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    active_cameras: Mapped[int] = mapped_column(Integer, default=0)
    fps_actual: Mapped[float] = mapped_column(Float, default=0.0)
    cpu_percent: Mapped[float] = mapped_column(Float, default=0.0)
    memory_mb: Mapped[float] = mapped_column(Float, default=0.0)

