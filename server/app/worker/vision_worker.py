"""
Vision AI Worker (Tahap 5)
Proses terpisah dari backend yang membaca stream video dari MediaMTX via FFmpeg,
menjalankan inferensi model YOLO (ONNX Runtime saja), melakukan pelacakan anonim,
mencatat benda untuk pencarian barang, kehadiran orang anonim, dan melaporkan heartbeat.

ATURAN KEJUJURAN:
- Menggunakan onnxruntime murni di runtime tanpa ultralytics.
- Menghormati mode privasi: jika privasi aktif, stream tidak dibaca sama sekali.
- Antrean berukuran 1: frame lama dibuang, tidak pernah ditumpuk.
- Thumbnail disimpan terenkripsi dengan AES-256-GCM.
"""

import asyncio
import datetime
import logging
import os
import shutil
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import httpx
import numpy as np
import onnxruntime as ort
import psutil
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from server.app.core.camera.encryption import encrypt_clip_data
from server.app.core.config import BASE_DIR, DATA_DIR, settings
from server.app.core.family.pose_engine import PoseEngine
from server.app.core.family.rules_engine import family_rules_engine
from server.app.models.camera import (
    AIWorkerHeartbeat,
    Camera,
    DetectedItemLog,
    PersonPresenceEvent,
)
from server.app.models.family import CameraZone, FamilyDailySummary, FamilyEventLog, FamilySettings

logger = logging.getLogger("vision_worker")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Kelas COCO 80 standar
COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator",
    "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
]


class AnonymousTracker:
    """Pelacak objek sederhana berbasis IoU untuk ID anonim antar frame."""

    def __init__(self, iou_threshold: float = 0.35, max_age_frames: int = 10):
        self.iou_threshold = iou_threshold
        self.max_age_frames = max_age_frames
        self.tracks: Dict[int, dict] = {}
        self.next_id: int = 1

    def update(self, detections: List[dict]) -> List[dict]:
        """
        detections: list of dict {'bbox': (x1, y1, x2, y2), 'class_name': str, 'score': float}
        Returns detections dengan tambahan 'track_id'
        """
        # Tingkatkan age semua track aktif
        for tid in list(self.tracks.keys()):
            self.tracks[tid]["age"] += 1
            if self.tracks[tid]["age"] > self.max_age_frames:
                del self.tracks[tid]

        assigned_detections = []
        used_tracks = set()

        for det in detections:
            bbox = det["bbox"]
            cname = det["class_name"]

            best_iou = 0.0
            best_tid = None

            for tid, tinfo in self.tracks.items():
                if tid in used_tracks or tinfo["class_name"] != cname:
                    continue
                iou = self._compute_iou(bbox, tinfo["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    best_tid = tid

            if best_iou >= self.iou_threshold and best_tid is not None:
                assigned_tid = best_tid
                used_tracks.add(best_tid)
                self.tracks[assigned_tid]["bbox"] = bbox
                self.tracks[assigned_tid]["age"] = 0
            else:
                assigned_tid = self.next_id
                self.next_id += 1
                self.tracks[assigned_tid] = {
                    "bbox": bbox,
                    "class_name": cname,
                    "age": 0,
                }
                used_tracks.add(assigned_tid)

            det_copy = dict(det)
            det_copy["track_id"] = assigned_tid
            assigned_detections.append(det_copy)

        return assigned_detections

    @staticmethod
    def _compute_iou(boxA: Tuple[float, float, float, float], boxB: Tuple[float, float, float, float]) -> float:
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interW = max(0.0, xB - xA)
        interH = max(0.0, yB - yA)
        interArea = interW * interH

        boxAArea = max(1e-5, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
        boxBArea = max(1e-5, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

        return interArea / float(boxAArea + boxBArea - interArea)


class VisionModelEngine:
    """Mesin inferensi YOLO murni berbasis ONNX Runtime."""

    def __init__(
        self,
        model_path: Path,
        input_size: int = 640,
        num_threads: int = 2,
        conf_thresh: float = 0.35,
        class_thresholds: Optional[dict[str, float]] = None,
    ):
        self.model_path = model_path
        self.input_size = input_size
        self.conf_thresh = conf_thresh
        self.class_thresholds = class_thresholds or {}

        opts = ort.SessionOptions()
        opts.intra_op_num_threads = num_threads
        opts.inter_op_num_threads = 1
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        logger.info(f"Memuat model YOLO ONNX dari {model_path} (threads={num_threads}, input_size={input_size})...")
        self.session = ort.InferenceSession(str(model_path), sess_options=opts, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name

    def detect(self, frame_bgr: np.ndarray) -> List[dict]:
        """Menjalankan deteksi objek pada satu frame BGR."""
        h_orig, w_orig = frame_bgr.shape[:2]

        # Preprocessing: resize ke input_size dan normalisasi
        img_resized = cv2.resize(frame_bgr, (self.input_size, self.input_size))
        blob = img_resized[:, :, ::-1].transpose(2, 0, 1).astype(np.float32) / 255.0
        blob = np.expand_dims(blob, axis=0)

        outputs = self.session.run(None, {self.input_name: blob})
        preds = outputs[0][0].T  # Bentuk: (N_proposals, 4 + 80)

        boxes = preds[:, :4]
        class_scores = preds[:, 4:]

        max_scores = np.max(class_scores, axis=1)
        class_ids = np.argmax(class_scores, axis=1)

        min_conf = min(self.conf_thresh, min(self.class_thresholds.values())) if self.class_thresholds else self.conf_thresh
        mask = max_scores >= min_conf
        filtered_boxes = boxes[mask]
        filtered_scores = max_scores[mask]
        filtered_cids = class_ids[mask]

        if len(filtered_boxes) == 0:
            return []

        # Konversi cx, cy, w, h ke x1, y1, x2, y2 skala piksel asli
        x_scale = w_orig / float(self.input_size)
        y_scale = h_orig / float(self.input_size)

        boxes_for_nms = []
        scores_for_nms = []
        classes_for_nms = []

        for b, s, c in zip(filtered_boxes, filtered_scores, filtered_cids):
            cx, cy, bw, bh = b
            x1 = (cx - bw / 2.0) * x_scale
            y1 = (cy - bh / 2.0) * y_scale
            w = bw * x_scale
            h = bh * y_scale

            boxes_for_nms.append([int(x1), int(y1), int(w), int(h)])
            scores_for_nms.append(float(s))
            classes_for_nms.append(int(c))

        indices = cv2.dnn.NMSBoxes(boxes_for_nms, scores_for_nms, min_conf, 0.45)
        if len(indices) == 0:
            return []

        results = []
        for idx in indices:
            i = int(idx[0]) if isinstance(idx, (list, tuple, np.ndarray)) else int(idx)
            cid = classes_for_nms[i]
            cname = COCO_CLASSES[cid] if 0 <= cid < len(COCO_CLASSES) else f"class_{cid}"
            score = scores_for_nms[i]

            # Cek ambang per kelas jika ditentukan
            target_thresh = self.class_thresholds.get(cname, self.conf_thresh)
            if score < target_thresh:
                continue

            bx, by, bw, bh = boxes_for_nms[i]
            x1 = max(0, bx)
            y1 = max(0, by)
            x2 = min(w_orig, bx + bw)
            y2 = min(h_orig, by + bh)

            results.append({
                "class_name": cname,
                "score": score,
                "bbox": (float(x1), float(y1), float(x2), float(y2)),
                "bbox_rel": (float(x1 / w_orig), float(y1 / h_orig), float((x2 - x1) / w_orig), float((y2 - y1) / h_orig)),
            })

        return results


class VisionWorker:
    """Worker utama yang mengelola kamera aktif, inferensi, database, dan heartbeat."""

    def __init__(
        self,
        worker_id: str = "vision_worker_1",
        db_url: Optional[str] = None,
        model_path: Optional[Path] = None,
    ):
        self.worker_id = worker_id
        self.db_url = db_url or settings.DATABASE_URL
        self.engine = create_async_engine(self.db_url, echo=False)
        self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

        resolved_model = model_path or (BASE_DIR / settings.VISION_MODEL_PATH)
        if not resolved_model.exists():
            # Fallback ke direktori lokal bila path relatif
            resolved_model = DATA_DIR / "models" / "yolo" / "yolo11n.onnx"

        self.model_engine = VisionModelEngine(
            model_path=resolved_model,
            input_size=settings.VISION_INPUT_SIZE,
            num_threads=settings.VISION_ONNX_THREADS,
            conf_thresh=settings.VISION_CONFIDENCE_THRESHOLD,
            class_thresholds=settings.VISION_CLASS_THRESHOLDS,
        )
        self.pose_engine = PoseEngine(
            num_threads=settings.VISION_ONNX_THREADS,
            conf_thresh=settings.VISION_CONFIDENCE_THRESHOLD,
        )
        self.last_pose_time: Dict[str, float] = {}
        self.trackers: Dict[str, AnonymousTracker] = {}
        self.active_presence: Dict[str, Optional[str]] = {}  # cam_id -> active presence event id
        self.is_running = False
        self.proc_self = psutil.Process()
        self.processed_frames_count = 0
        self.start_time = time.time()

    async def report_heartbeat(self, active_cams_count: int, fps_actual: float):
        """Kirim heartbeat periodik ke API server backend."""
        cpu_pct = self.proc_self.cpu_percent(interval=None)
        ram_mb = self.proc_self.memory_info().rss / (1024 * 1024)

        payload = {
            "worker_id": self.worker_id,
            "status": "online",
            "active_cameras": active_cams_count,
            "fps_actual": round(fps_actual, 2),
            "cpu_percent": round(cpu_pct, 1),
            "memory_mb": round(ram_mb, 1),
        }

        api_url = f"http://127.0.0.1:{settings.SERVER_PORT}/api/cameras/ai/heartbeat"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.post(api_url, json=payload)
                if resp.status_code != 200:
                    logger.warning(f"Heartbeat response status {resp.status_code}: {resp.text}")
        except Exception as e:
            # Jika API backend sibuk, fallback tulis langsung ke DB
            try:
                async with self.session_maker() as db:
                    stmt = select(AIWorkerHeartbeat).where(AIWorkerHeartbeat.id == self.worker_id)
                    hb = (await db.execute(stmt)).scalar_one_or_none()
                    if not hb:
                        hb = AIWorkerHeartbeat(id=self.worker_id)
                        db.add(hb)
                    hb.status = "online"
                    hb.active_cameras = active_cams_count
                    hb.fps_actual = fps_actual
                    hb.cpu_percent = cpu_pct
                    hb.memory_mb = ram_mb
                    hb.last_heartbeat = datetime.datetime.now(datetime.timezone.utc)
                    await db.commit()
            except Exception as dbe:
                logger.debug(f"Gagal menulis heartbeat lokal: {dbe}")

    async def get_active_cameras(self) -> List[Camera]:
        """Mengambil daftar kamera yang aktif, AI diaktifkan, dan mode privasi MATI."""
        async with self.session_maker() as db:
            stmt = select(Camera).where(
                Camera.status == "online",
                Camera.ai_enabled == True,
                Camera.privacy_mode == False,  # Privasi dihormati: kamera mode privasi tidak dibaca
            )
            return (await db.execute(stmt)).scalars().all()

    async def process_single_frame(
        self,
        camera_id: str,
        room_id: str,
        frame_bgr: np.ndarray,
        now: Optional[datetime.datetime] = None,
    ) -> List[dict]:
        """Memproses satu frame untuk kamera tertentu: deteksi, pelacakan, dedup benda, kehadiran orang."""
        if now is None:
            now = datetime.datetime.now(datetime.timezone.utc)

        detections = self.model_engine.detect(frame_bgr)
        if camera_id not in self.trackers:
            self.trackers[camera_id] = AnonymousTracker()

        tracked_detections = self.trackers[camera_id].update(detections)

        # 1. Hitung Kehadiran Orang Anonim
        person_detections = [d for d in tracked_detections if d["class_name"] == "person"]
        person_count = len(person_detections)
        await self._handle_person_presence(camera_id, person_count, now)

        # 2. Pose & Aturan Keluarga (Tahap 6): hanya pada frame yang ada orangnya (1-2 FPS)
        if person_count > 0:
            last_p_time = self.last_pose_time.get(camera_id, 0.0)
            cur_time = time.time()
            if (cur_time - last_p_time) >= 0.5:
                self.last_pose_time[camera_id] = cur_time
                poses = self.pose_engine.estimate_poses(frame_bgr)
                await self._evaluate_family_rules(camera_id, room_id, poses, tracked_detections, now)

        # 3. Log Benda Bernilai untuk Pencarian Barang
        trackable_classes = set(settings.VISION_TRACKABLE_CLASSES)
        items_to_log = [d for d in tracked_detections if d["class_name"] in trackable_classes]
        for item in items_to_log:
            await self._handle_item_log(camera_id, room_id, item, frame_bgr, now)

        self.processed_frames_count += 1
        return tracked_detections

    async def _evaluate_family_rules(
        self,
        camera_id: str,
        room_id: str,
        poses: List[dict],
        tracked_detections: List[dict],
        now: datetime.datetime,
    ):
        """Mengevaluasi aturan analitik keluarga per frame (Tahap 6)."""
        try:
            async with self.session_maker() as db:
                stmt_cfg = select(FamilySettings).where(FamilySettings.id == "default")
                fam_cfg = (await db.execute(stmt_cfg)).scalar_one_or_none()
                if not fam_cfg or not fam_cfg.enabled:
                    return

                stmt_z = select(CameraZone).where(CameraZone.camera_id == camera_id)
                zones = (await db.execute(stmt_z)).scalars().all()

                stmt_cam = select(Camera).where(Camera.id == camera_id)
                cam = (await db.execute(stmt_cam)).scalar_one_or_none()
                room_name = (cam.name if cam else room_id) or "Ruang"

                other_dets = [d for d in tracked_detections if d["class_name"] != "person"]

                new_events = await family_rules_engine.evaluate_frame(
                    camera_id=camera_id,
                    room_id=room_id,
                    room_name=room_name,
                    persons=poses,
                    other_detections=other_dets,
                    zones=zones,
                    current_settings=fam_cfg,
                    now=now,
                )

                for ev in new_events:
                    db.add(ev)
                if new_events:
                    await db.commit()
        except Exception as e:
            logger.debug(f"Error evaluating family rules: {e}")

    async def _handle_person_presence(self, camera_id: str, count: int, now: datetime.datetime):
        """Memperbarui atau membuat kejadian kehadiran orang anonim."""
        async with self.session_maker() as db:
            active_eid = self.active_presence.get(camera_id)
            if count > 0:
                if active_eid:
                    # Perbarui end_time dan jumlah maksimum orang
                    stmt = select(PersonPresenceEvent).where(PersonPresenceEvent.id == active_eid)
                    event = (await db.execute(stmt)).scalar_one_or_none()
                    if event:
                        event.end_time = now
                        if count > event.person_count:
                            event.person_count = count
                        await db.commit()
                else:
                    # Buat kejadian baru
                    new_event = PersonPresenceEvent(
                        id=str(uuid.uuid4()),
                        camera_id=camera_id,
                        start_time=now,
                        end_time=now,
                        person_count=count,
                    )
                    db.add(new_event)
                    await db.commit()
                    self.active_presence[camera_id] = new_event.id
            else:
                if active_eid:
                    # Tutup kejadian kehadiran orang
                    stmt = select(PersonPresenceEvent).where(PersonPresenceEvent.id == active_eid)
                    event = (await db.execute(stmt)).scalar_one_or_none()
                    if event:
                        event.end_time = now
                        await db.commit()
                    self.active_presence[camera_id] = None

    async def _handle_item_log(
        self,
        camera_id: str,
        room_id: str,
        item: dict,
        frame_bgr: np.ndarray,
        now: datetime.datetime,
    ):
        """Deduplikasi pencatatan benda dan pembuatan thumbnail terenkripsi AES-256-GCM."""
        cname = item["class_name"]
        tid = item.get("track_id")
        bx1, by1, bx2, by2 = item["bbox"]
        cx = (bx1 + bx2) / 2.0
        cy = (by1 + by2) / 2.0
        score = item["score"]

        async with self.session_maker() as db:
            # Cari log terakhir untuk kelas benda yang sama di kamera ini
            stmt = select(DetectedItemLog).where(
                DetectedItemLog.camera_id == camera_id,
                DetectedItemLog.class_name == cname,
            ).order_by(DetectedItemLog.last_seen_at.desc()).limit(1)

            recent_log = (await db.execute(stmt)).scalar_one_or_none()

            is_duplicate = False
            if recent_log:
                # Hitung jarak Euclidean pusat bounding box
                r_cx = recent_log.bbox_x + recent_log.bbox_w / 2.0
                r_cy = recent_log.bbox_y + recent_log.bbox_h / 2.0
                dist = np.sqrt((cx - r_cx) ** 2 + (cy - r_cy) ** 2)

                # Jika jarak < 50 piksel dan waktu terlihat dalam 5 menit terakhir -> barang diam
                last_dt = recent_log.last_seen_at
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=datetime.timezone.utc)
                time_diff = (now - last_dt).total_seconds()
                if dist < 50.0 and time_diff < 300.0:
                    is_duplicate = True
                    recent_log.last_seen_at = now
                    recent_log.confidence = max(recent_log.confidence, score)
                    await db.commit()

            if not is_duplicate:
                # Benda baru atau berpindah posisi signifikan: simpan thumbnail terenkripsi & buat log baru
                item_id = str(uuid.uuid4())
                thumb_path = await self._save_encrypted_thumbnail(camera_id, item_id, item["bbox"], frame_bgr)

                new_log = DetectedItemLog(
                    id=item_id,
                    camera_id=camera_id,
                    room_id=room_id,
                    class_name=cname,
                    track_id=tid,
                    first_seen_at=now,
                    last_seen_at=now,
                    bbox_x=bx1,
                    bbox_y=by1,
                    bbox_w=bx2 - bx1,
                    bbox_h=by2 - by1,
                    confidence=score,
                    thumbnail_path=str(thumb_path) if thumb_path else None,
                    source="stream",
                )
                db.add(new_log)
                await db.commit()

    async def _save_encrypted_thumbnail(
        self,
        camera_id: str,
        item_id: str,
        bbox: Tuple[float, float, float, float],
        frame_bgr: np.ndarray,
    ) -> Optional[Path]:
        """Memotong objek, mengubah ukuran menjadi thumbnail, dan mengenkripsi dengan AES-256-GCM."""
        h, w = frame_bgr.shape[:2]
        x1, y1, x2, y2 = bbox

        # Margin 15% di sekitar bounding box
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

        # Resize ke thumbnail maksimal 200x200
        thumb = cv2.resize(cropped, (200, 200))
        _, enc_jpg = cv2.imencode(".jpg", thumb, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        raw_bytes = enc_jpg.tobytes()

        # Enkripsi dengan AES-256-GCM (nonce 12-byte + ciphertext)
        ciphertext, nonce_hex = encrypt_clip_data(raw_bytes, camera_id)
        nonce_bytes = bytes.fromhex(nonce_hex)
        final_payload = nonce_bytes + ciphertext

        recordings_dir = Path(settings.RECORDING_STORAGE_DIR)
        recordings_dir.mkdir(parents=True, exist_ok=True)
        dest_path = recordings_dir / f"item_{item_id}.enc"
        dest_path.write_bytes(final_payload)

        return dest_path

    async def run_retention_cleanup(self):
        """Membersihkan log benda dan thumbnail yang lebih tua dari batas retensi konfigurasi."""
        retention_days = settings.VISION_ITEM_RETENTION_DAYS
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=retention_days)

        async with self.session_maker() as db:
            # 1. Hapus log lama
            stmt = select(DetectedItemLog).where(DetectedItemLog.last_seen_at < cutoff)
            expired_items = (await db.execute(stmt)).scalars().all()
            for it in expired_items:
                if it.thumbnail_path:
                    try:
                        p = Path(it.thumbnail_path)
                        if p.exists():
                            p.unlink()
                    except Exception:
                        pass
                await db.delete(it)

            # 2. Hapus kejadian kehadiran orang lama
            stmt_pres = delete(PersonPresenceEvent).where(PersonPresenceEvent.start_time < cutoff)
            await db.execute(stmt_pres)

            # 3. Batasi total baris DetectedItemLog agar tidak melebihi kuota
            max_records = settings.VISION_MAX_ITEM_RECORDS
            count_stmt = select(func.count()).select_from(DetectedItemLog)
            total_records = (await db.execute(count_stmt)).scalar() or 0
            if total_records > max_records:
                excess = total_records - max_records
                sub_stmt = select(DetectedItemLog.id).order_by(DetectedItemLog.first_seen_at.asc()).limit(excess)
                old_ids = (await db.execute(sub_stmt)).scalars().all()
                if old_ids:
                    del_stmt = delete(DetectedItemLog).where(DetectedItemLog.id.in_(old_ids))
                    await db.execute(del_stmt)

            # 4. Hapus kejadian dan statistik keluarga yang melampaui retensi
            stmt_cfg = select(FamilySettings).where(FamilySettings.id == "default")
            fam_cfg = (await db.execute(stmt_cfg)).scalar_one_or_none()
            ev_retention = fam_cfg.events_retention_days if fam_cfg else settings.FAMILY_EVENTS_RETENTION_DAYS
            st_retention = fam_cfg.stats_retention_days if fam_cfg else settings.FAMILY_STATS_RETENTION_DAYS

            cutoff_events = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=ev_retention)
            cutoff_stats = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=st_retention)).strftime("%Y-%m-%d")

            stmt_del_fam_ev = delete(FamilyEventLog).where(FamilyEventLog.created_at < cutoff_events)
            await db.execute(stmt_del_fam_ev)

            stmt_del_fam_st = delete(FamilyDailySummary).where(FamilyDailySummary.date < cutoff_stats)
            await db.execute(stmt_del_fam_st)

            await db.commit()
            logger.info("Pembersihan retensi log benda dan data keluarga selesai.")


async def run_worker_main():
    """Loop eksekusi utama worker AI."""
    logger.info("Memulai Standalone Vision AI Worker (Tahap 5)...")
    worker = VisionWorker()
    worker.is_running = True

    # Temukan path ffmpeg
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        custom_ffmpeg = settings.BASE_DIR / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"
        if custom_ffmpeg.exists():
            ffmpeg_bin = str(custom_ffmpeg)
        else:
            ffmpeg_bin = "ffmpeg"

    active_streams: Dict[str, subprocess.Popen] = {}
    fps_sample_count = 0
    fps_sample_start = time.time()

    try:
        while worker.is_running:
            cams = await worker.get_active_cameras()
            active_ids = {c.id for c in cams}

            # Tutup stream kamera yang dinonaktifkan atau masuk mode privasi
            for cid in list(active_streams.keys()):
                if cid not in active_ids:
                    logger.info(f"Menghentikan pembacaan stream {cid} (mode privasi aktif atau dinonaktifkan)...")
                    proc = active_streams.pop(cid)
                    proc.terminate()
                    try:
                        proc.wait(timeout=1.0)
                    except Exception:
                        proc.kill()

            # Buka stream untuk kamera yang baru aktif
            for cam in cams:
                if cam.id not in active_streams:
                    rtsp_url = f"{settings.MEDIAMTX_RTSP_URL}/{cam.id}?password=internal_worker"
                    cmd = [
                        ffmpeg_bin,
                        "-rtsp_transport", "tcp",
                        "-i", rtsp_url,
                        "-vf", f"fps={settings.VISION_TARGET_FPS},scale={settings.VISION_INPUT_SIZE}:{settings.VISION_INPUT_SIZE}",
                        "-f", "rawvideo",
                        "-pix_fmt", "bgr24",
                        "pipe:1",
                    ]
                    try:
                        sub = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=settings.VISION_INPUT_SIZE * settings.VISION_INPUT_SIZE * 3)
                        active_streams[cam.id] = sub
                        logger.info(f"Stream kamera {cam.id} terhubung ke AI worker (PID {sub.pid}).")
                    except Exception as e:
                        logger.error(f"Gagal membuka FFmpeg pipe untuk {cam.id}: {e}")

            # Baca satu frame per kamera aktif (antrean berukuran 1: drop frame lama)
            frame_sz = settings.VISION_INPUT_SIZE * settings.VISION_INPUT_SIZE * 3
            now_dt = datetime.datetime.now(datetime.timezone.utc)

            for cam in cams:
                sub = active_streams.get(cam.id)
                if not sub or sub.poll() is not None:
                    continue

                try:
                    # Baca persis frame_sz bytes
                    raw_data = bytearray(frame_sz)
                    mv = memoryview(raw_data)
                    bytes_read = 0
                    while bytes_read < frame_sz:
                        chunk = sub.stdout.readinto(mv[bytes_read:])
                        if chunk == 0:
                            break
                        bytes_read += chunk

                    if bytes_read == frame_sz:
                        frame = np.frombuffer(raw_data, dtype=np.uint8).reshape((settings.VISION_INPUT_SIZE, settings.VISION_INPUT_SIZE, 3))
                        await worker.process_single_frame(cam.id, cam.room_id or "default", frame, now_dt)
                        fps_sample_count += 1
                except Exception as fe:
                    logger.error(f"Error membaca frame {cam.id}: {fe}")

            # Hitung FPS aktual
            elapsed = time.time() - fps_sample_start
            fps_actual = (fps_sample_count / elapsed) if elapsed >= 1.0 else 0.0
            if elapsed >= 5.0:
                await worker.report_heartbeat(len(active_streams), fps_actual)
                fps_sample_count = 0
                fps_sample_start = time.time()

            await asyncio.sleep(0.01)

    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Worker AI dihentikan oleh pengguna.")
    finally:
        for cid, proc in active_streams.items():
            try:
                proc.terminate()
            except Exception:
                pass
        await worker.engine.dispose()
        logger.info("Worker AI berhasil dimatikan.")


if __name__ == "__main__":
    asyncio.run(run_worker_main())
