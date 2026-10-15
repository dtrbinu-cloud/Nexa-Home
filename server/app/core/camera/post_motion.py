"""
Layanan Deteksi Barang Pasca-Gerakan (Tahap 5 Perbaikan 4).
Ketika gerakan di sebuah kamera berhenti selama N detik (default 5s),
menjalankan SATU kali deteksi barang yang lebih teliti pada frame resolusi penuh
menggunakan model YOLO11s 640 FP32 (ONNX Runtime, 2 threads).
Log benda yang dihasilkan ditandai dengan source="post_motion".
"""

import asyncio
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import uuid

import cv2
import numpy as np
from sqlalchemy import select

from server.app.core.camera.encryption import encrypt_clip_data
from server.app.core.config import BASE_DIR, DATA_DIR, settings
from server.app.core.database import async_session_factory
from server.app.models.camera import Camera, DetectedItemLog
from server.app.worker.vision_worker import VisionModelEngine

logger = logging.getLogger("server.camera.post_motion")

# Cache mesin YOLO11s agar tidak memuat ulang model dari disk pada setiap pass
_post_motion_engine: Optional[VisionModelEngine] = None


def get_post_motion_engine() -> Optional[VisionModelEngine]:
    """Mengambil instance singleton VisionModelEngine untuk YOLO11s FP32."""
    global _post_motion_engine
    if _post_motion_engine is None:
        model_path = BASE_DIR / settings.VISION_POST_MOTION_MODEL_PATH
        if not model_path.exists():
            model_path = DATA_DIR / "models" / "yolo" / "yolo11s_640.onnx"
        if not model_path.exists():
            logger.warning(f"Model post-motion YOLO11s tidak ditemukan di {model_path}.")
            return None

        logger.info(f"Menginisialisasi PostMotion Engine dengan model: {model_path}")
        _post_motion_engine = VisionModelEngine(
            model_path=model_path,
            input_size=settings.VISION_INPUT_SIZE,
            num_threads=settings.VISION_ONNX_THREADS,
            conf_thresh=settings.VISION_POST_MOTION_CONFIDENCE,
            class_thresholds=settings.VISION_CLASS_THRESHOLDS,
        )
    return _post_motion_engine


async def execute_post_motion_detection(
    camera_id: str,
    frame_bgr: np.ndarray,
    room_id: Optional[str] = None,
) -> List[dict]:
    """
    Menjalankan 1 pass deteksi teliti pasca-gerakan pada frame resolusi penuh.
    Menyimpan hasil ke database dengan source='post_motion'.
    """
    if not settings.VISION_POST_MOTION_ENABLED:
        return []

    engine = get_post_motion_engine()
    if engine is None:
        return []

    now = datetime.now(timezone.utc)

    # Dapatkan room_id dari database jika belum diberikan
    if not room_id:
        async with async_session_factory() as db:
            cam = await db.get(Camera, camera_id)
            if cam:
                room_id = cam.room_id or "default"
            else:
                room_id = "default"

    # Jalankan inferensi 1 pass
    loop = asyncio.get_running_loop()
    detections = await loop.run_in_executor(None, engine.detect, frame_bgr)

    trackable = set(settings.VISION_TRACKABLE_CLASSES)
    items_found = [d for d in detections if d["class_name"] in trackable]

    if not items_found:
        logger.debug(f"[Post-Motion] Kamera {camera_id}: Tidak ada barang terdeteksi pada pass pasca-gerakan.")
        return []

    logger.info(
        f"[Post-Motion] Kamera {camera_id}: Berhasil mendeteksi {len(items_found)} barang pada pass pasca-gerakan (YOLO11s)."
    )

    async with async_session_factory() as db:
        for item in items_found:
            cname = item["class_name"]
            score = item["score"]
            bx1, by1, bx2, by2 = item["bbox"]
            cx = (bx1 + bx2) / 2.0
            cy = (by1 + by2) / 2.0

            # Cek log terakhir untuk dedup
            stmt = select(DetectedItemLog).where(
                DetectedItemLog.camera_id == camera_id,
                DetectedItemLog.class_name == cname,
            ).order_by(DetectedItemLog.last_seen_at.desc()).limit(1)

            recent_log = (await db.execute(stmt)).scalar_one_or_none()
            is_duplicate = False

            if recent_log:
                r_cx = recent_log.bbox_x + recent_log.bbox_w / 2.0
                r_cy = recent_log.bbox_y + recent_log.bbox_h / 2.0
                dist = np.sqrt((cx - r_cx) ** 2 + (cy - r_cy) ** 2)

                last_dt = recent_log.last_seen_at
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                time_diff = (now - last_dt).total_seconds()

                if dist < 50.0 and time_diff < 300.0:
                    is_duplicate = True
                    recent_log.last_seen_at = now
                    recent_log.confidence = max(recent_log.confidence, score)
                    # Catat bahwa benda terverifikasi kembali lewat pass post_motion
                    recent_log.source = "post_motion"
                    await db.commit()

            if not is_duplicate:
                item_id = str(uuid.uuid4())
                thumb_path = await _save_encrypted_thumbnail(camera_id, item_id, item["bbox"], frame_bgr)

                new_log = DetectedItemLog(
                    id=item_id,
                    camera_id=camera_id,
                    room_id=room_id,
                    class_name=cname,
                    track_id=None,
                    first_seen_at=now,
                    last_seen_at=now,
                    bbox_x=bx1,
                    bbox_y=by1,
                    bbox_w=bx2 - bx1,
                    bbox_h=by2 - by1,
                    confidence=score,
                    thumbnail_path=str(thumb_path) if thumb_path else None,
                    source="post_motion",
                )
                db.add(new_log)
                await db.commit()

    return items_found


async def _save_encrypted_thumbnail(
    camera_id: str,
    item_id: str,
    bbox: Tuple[float, float, float, float],
    frame_bgr: np.ndarray,
) -> Optional[Path]:
    """Menyimpan thumbnail terenkripsi AES-256-GCM."""
    h, w = frame_bgr.shape[:2]
    x1, y1, x2, y2 = bbox
    bw = x2 - x1
    bh = y2 - y1
    margin_x = int(bw * 0.15)
    margin_y = int(bh * 0.15)

    crop_x1 = max(0, int(x1 - margin_x))
    crop_y1 = max(0, int(y1 - margin_y))
    crop_x2 = min(w, int(x2 + margin_x))
    crop_y2 = min(h, int(y2 + margin_y))

    cropped = frame_bgr[crop_y1:crop_y2, crop_x1:crop_x2]
    if cropped.size == 0:
        return None

    thumb = cv2.resize(cropped, (200, 200))
    _, enc_jpg = cv2.imencode(".jpg", thumb, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    raw_bytes = enc_jpg.tobytes()

    ciphertext, nonce_hex = encrypt_clip_data(raw_bytes, camera_id)
    nonce_bytes = bytes.fromhex(nonce_hex)
    final_payload = nonce_bytes + ciphertext

    recordings_dir = Path(settings.RECORDING_STORAGE_DIR)
    recordings_dir.mkdir(parents=True, exist_ok=True)
    dest_path = recordings_dir / f"item_{item_id}.enc"
    dest_path.write_bytes(final_payload)
    return dest_path
