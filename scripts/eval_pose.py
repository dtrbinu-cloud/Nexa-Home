#!/usr/bin/env python3
"""
scripts/eval_pose.py
Skrip Evaluasi Model Estimasi Pose & Deteksi Jatuh (Tahap 6).
Mendukung input rekaman video kustom pengguna (--video dan --labels).

Format Anotasi Label JSON (--labels):
[
  {
    "frame_idx": 10,
    "bbox": [x1, y1, x2, y2],
    "posture": "duduk" | "berdiri" | "berbaring" | "tidak diketahui",
    "is_fall": false
  },
  ...
]

ATURAN KEJUJURAN:
- Menggunakan onnxruntime murni.
- Jika rekaman publik (seperti UR Fall Detection Dataset) tidak diunduh/tersedia lokal,
  skrip ini disediakan agar pengguna dapat menguji rekamannya sendiri secara reproducible.
"""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
import time
from typing import Optional

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server.app.core.family.pose_engine import PoseEngine


def evaluate_video(
    engine: PoseEngine,
    video_path: Path,
    labels_path: Optional[Path] = None,
    output_annotated: Optional[Path] = None,
    max_frames: Optional[int] = None,
):
    print(f"[*] Membuka video: {video_path}...", flush=True)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"[ERROR] Gagal membuka video: {video_path}", flush=True)
        sys.exit(1)

    labels_by_frame = {}
    if labels_path and labels_path.exists():
        with open(labels_path, "r", encoding="utf-8") as f:
            raw_labels = json.load(f)
            for item in raw_labels:
                f_idx = item.get("frame_idx", 0)
                labels_by_frame.setdefault(f_idx, []).append(item)
        print(f"[*] Memuat {len(raw_labels)} anotasi ground truth.", flush=True)

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    target_count = min(total_frames, max_frames) if max_frames else total_frames
    print(f"[*] Total frames: {target_count} dari {total_frames} (FPS: {fps:.1f})", flush=True)

    frame_idx = 0
    t0 = time.time()
    inference_times = []

    # Confusion matrix untuk postur
    # GT posture -> Pred posture -> count
    confusion_matrix = defaultdict(lambda: defaultdict(int))
    total_persons_detected = 0

    while True:
        if max_frames and frame_idx >= max_frames:
            break
        ret, frame = cap.read()
        if not ret:
            break

        inf_t0 = time.time()
        poses = engine.estimate_poses(frame)
        inf_elapsed = time.time() - inf_t0
        inference_times.append(inf_elapsed)

        total_persons_detected += len(poses)

        # Cocokkan dengan labels jika ada
        gt_items = labels_by_frame.get(frame_idx, [])
        for p in poses:
            pred_posture = p["posture"]
            if gt_items:
                # Cocokkan dengan IoU terbaik terhadap GT bbox
                bx = p["bbox"]
                best_gt = None
                best_iou = 0.0
                for g in gt_items:
                    g_box = g.get("bbox", [0, 0, 0, 0])
                    iou = compute_iou(bx, g_box)
                    if iou > best_iou:
                        best_iou = iou
                        best_gt = g
                if best_gt and best_iou >= 0.4:
                    gt_posture = best_gt.get("posture", "tidak diketahui")
                    confusion_matrix[gt_posture][pred_posture] += 1
            else:
                confusion_matrix["unlabeled"][pred_posture] += 1

        frame_idx += 1
        if frame_idx % 50 == 0 or frame_idx == total_frames:
            print(f"  -> Diproses {frame_idx}/{total_frames} frame ({(frame_idx/total_frames)*100:.1f}%)...")

    cap.release()
    total_elapsed = time.time() - t0
    avg_latency_ms = (sum(inference_times) / len(inference_times) * 1000.0) if inference_times else 0.0

    print("\n" + "=" * 80)
    print("HASIL EVALUASI POSE & POSTUR")
    print("=" * 80)
    print(f"Total frame diproses       : {frame_idx}")
    print(f"Total waktu eksekusi       : {total_elapsed:.2f} detik")
    print(f"Rata-rata waktu inferensi  : {avg_latency_ms:.1f} ms / frame ({1000.0/max(1e-3, avg_latency_ms):.2f} FPS)")
    print(f"Total orang terdeteksi     : {total_persons_detected}")

    if labels_by_frame:
        print("\nCONFUSION MATRIX POSTUR (Ground Truth vs Prediksi):")
        all_postures = ["duduk", "berdiri", "berbaring", "tidak diketahui"]
        gt_pred_title = "GT \\ Pred"
        header = f"{gt_pred_title:<16} | " + " | ".join(f"{p:<12}" for p in all_postures)
        print("-" * len(header))
        print(header)
        print("-" * len(header))

        for gt_p in all_postures:
            row_vals = [confusion_matrix[gt_p][pred_p] for pred_p in all_postures]
            row_str = f"{gt_p:<16} | " + " | ".join(f"{v:<12}" for v in row_vals)
            print(row_str)
        print("-" * len(header))

        # Precision & Recall per class
        print("\nMETRIK PER KELAS POSTUR:")
        print(f"{'Postur':<16} | {'Precision':<12} | {'Recall':<12} | {'F1-Score':<12}")
        print("-" * 56)
        for p in all_postures:
            tp = confusion_matrix[p][p]
            fp = sum(confusion_matrix[other][p] for other in all_postures if other != p)
            fn = sum(confusion_matrix[p][other] for other in all_postures if other != p)

            prec = (tp / float(tp + fp)) if (tp + fp) > 0 else 0.0
            rec = (tp / float(tp + fn)) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
            print(f"{p:<16} | {prec*100:>10.2f}% | {rec*100:>10.2f}% | {f1*100:>10.2f}%")
        print("-" * 56)
    else:
        print("\nDISTRIBUSI PREDIKSI POSTUR (Tanpa Anotasi Label GT):")
        for pred_p, count in confusion_matrix["unlabeled"].items():
            pct = (count / max(1, total_persons_detected)) * 100
            print(f"  - {pred_p:<16}: {count} deteksi ({pct:.1f}%)")


def compute_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
    boxAArea = max(1e-5, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
    boxBArea = max(1e-5, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))
    return interArea / float(boxAArea + boxBArea - interArea)


def main():
    parser = argparse.ArgumentParser(description="Evaluasi Pose & Postur Tubuh YOLO11n-pose")
    parser.add_argument("--video", type=str, required=True, help="Path ke file video rekaman")
    parser.add_argument("--labels", type=str, default=None, help="Path ke file anotasi JSON (opsional)")
    parser.add_argument("--max-frames", type=int, default=None, help="Batas maksimal frame yang dievaluasi")
    args = parser.parse_args()

    v_path = Path(args.video)
    if not v_path.exists():
        print(f"[ERROR] Video tidak ditemukan di: {v_path}")
        sys.exit(1)

    lbl_path = Path(args.labels) if args.labels else None

    print("[*] Menginisialisasi PoseEngine...", flush=True)
    engine = PoseEngine(num_threads=2, conf_thresh=0.35)

    evaluate_video(engine, v_path, lbl_path, max_frames=args.max_frames)


if __name__ == "__main__":
    main()
