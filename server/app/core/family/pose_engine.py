"""
Mesin Estimasi Pose dan Klasifikasi Postur Tubuh (Tahap 6).
- Model: YOLO11n-pose FP32 (ONNX Runtime, 2 threads intra-op).
- Keypoints: 17 titik tubuh standar COCO Pose (hidung, mata, telinga, bahu, siku, pergelangan tangan, pinggul, lutut, pergelangan kaki).
- Klasifikasi postur diturunkan dari proporsi geometri tubuh:
  * "berbaring": torso mendatar (sudut horizontal) atau rasio aspek bbox lebar > 1.2
  * "duduk": pinggul dan lutut berada pada ketinggian horizontal yang berdekatan atau torso tegak dengan tungkai horizontal
  * "berdiri": postur tegak vertikal dengan ekstensi kaki lurus ke bawah
  * "tidak diketahui": keypoint penting terhalang atau keyakinan rendah
"""

import math
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
import onnxruntime as ort

from server.app.core.config import BASE_DIR, DATA_DIR, settings


class PoseEngine:
    """Mesin inferensi YOLO11n-pose berbasis ONNX Runtime."""

    def __init__(
        self,
        model_path: Optional[Path] = None,
        input_size: int = 640,
        num_threads: int = 2,
        conf_thresh: float = 0.35,
    ):
        self.input_size = input_size
        self.conf_thresh = conf_thresh

        resolved = model_path
        if resolved is None or not resolved.exists():
            resolved = BASE_DIR / settings.VISION_POSE_MODEL_PATH
        if not resolved.exists():
            resolved = DATA_DIR / "models" / "yolo" / "yolo11n-pose.onnx"
        if not resolved.exists():
            resolved = BASE_DIR / "yolo11n-pose.onnx"

        self.model_path = resolved

        opts = ort.SessionOptions()
        opts.intra_op_num_threads = num_threads
        opts.inter_op_num_threads = 1
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        self.session = ort.InferenceSession(str(self.model_path), sess_options=opts, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name

    def estimate_poses(self, frame_bgr: np.ndarray) -> List[dict]:
        """
        Menjalankan estimasi pose pada frame BGR.
        Hanya mengembalikan deteksi orang dengan keypoints dan postur yang diturunkan.
        """
        h_orig, w_orig = frame_bgr.shape[:2]

        # Preprocessing: resize dan normalisasi
        img_resized = cv2.resize(frame_bgr, (self.input_size, self.input_size))
        blob = img_resized[:, :, ::-1].transpose(2, 0, 1).astype(np.float32) / 255.0
        blob = np.expand_dims(blob, axis=0)

        outputs = self.session.run(None, {self.input_name: blob})
        preds = outputs[0][0].T  # Bentuk: (8400, 56)

        boxes = preds[:, :4]
        scores = preds[:, 4]
        raw_kpts = preds[:, 5:]  # 51 features = 17 * 3

        mask = scores >= self.conf_thresh
        filtered_boxes = boxes[mask]
        filtered_scores = scores[mask]
        filtered_kpts = raw_kpts[mask]

        if len(filtered_boxes) == 0:
            return []

        x_scale = w_orig / float(self.input_size)
        y_scale = h_orig / float(self.input_size)

        boxes_for_nms = []
        scores_for_nms = []
        kpts_list = []

        for b, s, kp in zip(filtered_boxes, filtered_scores, filtered_kpts):
            cx, cy, bw, bh = b
            x1 = (cx - bw / 2.0) * x_scale
            y1 = (cy - bh / 2.0) * y_scale
            w = bw * x_scale
            h = bh * y_scale

            boxes_for_nms.append([int(x1), int(y1), int(w), int(h)])
            scores_for_nms.append(float(s))
            kpts_list.append(kp)

        indices = cv2.dnn.NMSBoxes(boxes_for_nms, scores_for_nms, self.conf_thresh, 0.45)
        if len(indices) == 0:
            return []

        results = []
        for idx in indices:
            i = int(idx[0]) if isinstance(idx, (list, tuple, np.ndarray)) else int(idx)
            bx, by, bw, bh = boxes_for_nms[i]
            x1 = max(0.0, float(bx))
            y1 = max(0.0, float(by))
            x2 = min(float(w_orig), float(bx + bw))
            y2 = min(float(h_orig), float(by + bh))

            # Reshape 17 keypoints (x, y, conf)
            kp_raw = kpts_list[i].reshape(17, 3)
            scaled_kpts = []
            for kx, ky, kc in kp_raw:
                scaled_kpts.append([
                    float(kx * x_scale),
                    float(ky * y_scale),
                    float(kc),
                ])

            posture = classify_posture((x1, y1, x2, y2), scaled_kpts)
            foot_x = (x1 + x2) / 2.0
            foot_y = y2

            results.append({
                "bbox": (x1, y1, x2, y2),
                "bbox_rel": (x1 / w_orig, y1 / h_orig, (x2 - x1) / w_orig, (y2 - y1) / h_orig),
                "score": scores_for_nms[i],
                "keypoints": scaled_kpts,
                "posture": posture,
                "foot_point": (foot_x, foot_y),
                "foot_point_rel": (foot_x / w_orig, foot_y / h_orig),
            })

        return results


def classify_posture(bbox: Tuple[float, float, float, float], keypoints: List[List[float]]) -> str:
    """
    Menurunkan postur ('duduk', 'berdiri', 'berbaring', 'tidak diketahui') dari keypoints dan bbox.

    Indeks keypoints COCO:
    0: nose, 1-2: eyes, 3-4: ears
    5: left_shoulder, 6: right_shoulder
    7: left_elbow, 8: right_elbow
    9: left_wrist, 10: right_wrist
    11: left_hip, 12: right_hip
    13: left_knee, 14: right_knee
    15: left_ankle, 16: right_ankle
    """
    x1, y1, x2, y2 = bbox
    box_w = max(1.0, x2 - x1)
    box_h = max(1.0, y2 - y1)
    aspect_ratio = box_w / box_h

    # Ekstraksi titik penting jika keyakinan >= 0.25
    kpts = np.array(keypoints)  # shape (17, 3)

    conf_thresh = 0.25

    def get_avg_point(idx1: int, idx2: int) -> Optional[Tuple[float, float]]:
        p1 = kpts[idx1]
        p2 = kpts[idx2]
        valid = []
        if p1[2] >= conf_thresh:
            valid.append((p1[0], p1[1]))
        if p2[2] >= conf_thresh:
            valid.append((p2[0], p2[1]))
        if not valid:
            return None
        avg_x = sum(p[0] for p in valid) / len(valid)
        avg_y = sum(p[1] for p in valid) / len(valid)
        return avg_x, avg_y

    shoulder = get_avg_point(5, 6)
    hip = get_avg_point(11, 12)
    knee = get_avg_point(13, 14)
    ankle = get_avg_point(15, 16)

    # 1. KASUS BERBARING (Lying Down / Fall)
    # - Rasio kotak lebar terhadap tinggi > 1.25, ATAU
    # - Kemiringan torso (bahu ke pinggul) mendatar: |dy| <= |dx| * 0.8
    if aspect_ratio >= 1.20:
        return "berbaring"

    if shoulder is not None and hip is not None:
        dx_torso = abs(shoulder[0] - hip[0])
        dy_torso = abs(shoulder[1] - hip[1])
        if dy_torso < (dx_torso * 0.85):
            return "berbaring"

    # Jika tidak ada titik bahu dan pinggul, periksa keyakinan
    confident_count = sum(1 for kp in kpts if kp[2] >= conf_thresh)
    if confident_count < 4:
        return "tidak diketahui"

    # 2. KASUS DUDUK vs BERDIRI
    if shoulder is not None and hip is not None:
        torso_height = abs(shoulder[1] - hip[1])

        # Jika ada lutut
        if knee is not None:
            thigh_dy = abs(knee[1] - hip[1])
            # Pada postur duduk, paha mendatar sehingga perbedaan tinggi vertikal pinggul dan lutut kecil
            # dibandingkan dengan tinggi torso
            if thigh_dy < (0.45 * torso_height) and aspect_ratio >= 0.50:
                return "duduk"

        # Jika ada pergelangan kaki
        if ankle is not None:
            leg_height = abs(ankle[1] - hip[1])
            # Berdiri: kaki memanjang vertikal signifikan
            if leg_height > (0.85 * torso_height) and aspect_ratio < 0.65:
                return "berdiri"
            # Duduk: kaki tertekuk atau pendek terhadap rasio kotak
            if leg_height <= (0.85 * torso_height) or aspect_ratio >= 0.65:
                return "duduk"

        # Fallback berbasis rasio aspek ketika keypoints kaki terpotong/occluded
        if aspect_ratio >= 0.60:
            return "duduk"
        else:
            return "berdiri"

    # Fallback berbasis rasio kotak
    if aspect_ratio < 0.60:
        return "berdiri"
    elif aspect_ratio < 1.15:
        return "duduk"
    else:
        return "berbaring"
