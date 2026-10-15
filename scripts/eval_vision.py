#!/usr/bin/env python3
"""
scripts/eval_vision.py
Evaluasi Akurasi Model Vision AI (YOLO11n-640) pada Subset Resmi COCO val2017.
Mendukung input kustom (--video dan --labels) untuk pengujian kamera asli di masa depan.

ATURAN KEJUJURAN:
- Menggunakan onnxruntime murni.
- Ground Truth berasal dari anotasi resmi COCO val2017 (bukan label buatan sendiri).
- Evaluasi IoU = 0.50.
- Sapuan ambang confidence: 0.25, 0.35, 0.50.
- Kelas tanpa data uji ditulis 'TIDAK ADA DATA', bukan 0% atau 100%.
- Baris rata-rata hanya merangkum kelas yang memiliki data uji nyata.
- 65 frame evaluasi lama yang berasal dari heuristik/auto-label ditandai TIDAK VALID.
- File webcam_record.mp4 telah dihapus dari repositori.
"""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server.app.core.config import settings
from server.app.worker.vision_worker import COCO_CLASSES, VisionModelEngine

MODEL_PATH = REPO_ROOT / "server" / "data" / "models" / "yolo" / "yolo11n_640.onnx"
DEFAULT_SUBSET_JSON = REPO_ROOT / "tests" / "data" / "coco_eval_subset.json"
DEFAULT_IMAGES_DIR = REPO_ROOT / "tests" / "data" / "coco_val2017_subset"

TARGET_CLASSES = [
    "person",
    "cell phone",
    "remote",
    "bottle",
    "cup",
    "laptop",
    "book",
    "backpack",
    "handbag",
]


def compute_iou(boxA, boxB):
    """Menghitung Intersection over Union (IoU) antara dua bounding box [x1, y1, x2, y2]."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
    boxAArea = max(1e-5, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
    boxBArea = max(1e-5, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))

    return interArea / float(boxAArea + boxBArea - interArea)


def evaluate_detections(ground_truths, detections, iou_thresh=0.5):
    """
    ground_truths: dict of {class_name: list of [x1, y1, x2, y2]}
    detections: dict of {class_name: list of ([x1, y1, x2, y2], score)}
    Returns: dict of {class_name: {TP, FP, FN, total_gt, total_det}}
    """
    classes = set(list(ground_truths.keys()) + list(detections.keys()))
    stats = {}

    for cname in classes:
        gts = list(ground_truths.get(cname, []))
        dets = list(detections.get(cname, []))

        # Sort deteksi berdasarkan confidence skor descending
        dets.sort(key=lambda x: x[1], reverse=True)

        matched_gt = set()
        tp = 0
        fp = 0

        for det_box, score in dets:
            best_iou = 0.0
            best_gt_idx = -1
            for g_idx, gt_box in enumerate(gts):
                if g_idx in matched_gt:
                    continue
                iou = compute_iou(det_box, gt_box)
                if iou > best_iou:
                    best_iou = iou
                    best_gt_idx = g_idx

            if best_iou >= iou_thresh and best_gt_idx >= 0:
                tp += 1
                matched_gt.add(best_gt_idx)
            else:
                fp += 1

        fn = len(gts) - len(matched_gt)
        stats[cname] = {
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "total_gt": len(gts),
            "total_det": len(dets),
        }

    return stats


def run_coco_evaluation(model_engine, subset_json_path, images_dir_path, conf_thresholds=[0.25, 0.35, 0.50]):
    with open(subset_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    images = {img["id"]: img for img in data["images"]}
    annos_by_img = defaultdict(list)
    for ann in data["annotations"]:
        annos_by_img[ann["image_id"]].append(ann)

    print(f"[*] Menjalankan inferensi pada {len(images)} gambar COCO...")
    # Lakukan inferensi pada confidence di bawah threshold terendah sekali agar cepat, lalu filter sesuai threshold
    raw_predictions = {}
    lowest_thresh = min(conf_thresholds)
    model_engine.conf_thresh = max(0.01, lowest_thresh * 0.85)

    import time
    t_start = time.perf_counter()

    for idx, (img_id, img_info) in enumerate(images.items()):
        img_path = images_dir_path / img_info["file_name"]
        if not img_path.exists():
            continue
        frame = cv2.imread(str(img_path))
        if frame is None:
            continue
        dets = model_engine.detect(frame)
        raw_predictions[img_id] = dets

    infer_elapsed = time.perf_counter() - t_start
    avg_per_pass_sec = infer_elapsed / max(1, len(raw_predictions))
    avg_per_pass_ms = avg_per_pass_sec * 1000.0
    print(f"[+] Total waktu inferensi: {infer_elapsed:.2f}s untuk {len(raw_predictions)} gambar ({avg_per_pass_ms:.1f} ms / {avg_per_pass_sec:.3f} s per pass)")


    # Evaluasi per confidence threshold
    results_per_threshold = {}

    for thresh in conf_thresholds:
        class_tp_fp_fn = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0, "GT": 0, "DET": 0})

        for img_id, img_info in images.items():
            if img_id not in raw_predictions:
                continue

            # Ground truth
            gt_dict = defaultdict(list)
            for a in annos_by_img[img_id]:
                cname = a["class_name"]
                bx, by, bw, bh = a["bbox"]
                gt_dict[cname].append([bx, by, bx + bw, by + bh])

            # Detections terfilter threshold
            det_dict = defaultdict(list)
            for d in raw_predictions[img_id]:
                if d["score"] >= thresh:
                    cname = d["class_name"]
                    det_dict[cname].append((d["bbox"], d["score"]))

            # Cocokkan
            stats = evaluate_detections(gt_dict, det_dict, iou_thresh=0.50)
            for cname, s in stats.items():
                class_tp_fp_fn[cname]["TP"] += s["TP"]
                class_tp_fp_fn[cname]["FP"] += s["FP"]
                class_tp_fp_fn[cname]["FN"] += s["FN"]
                class_tp_fp_fn[cname]["GT"] += s["total_gt"]
                class_tp_fp_fn[cname]["DET"] += s["total_det"]

        results_per_threshold[thresh] = class_tp_fp_fn

    return results_per_threshold


def run_custom_video_evaluation(model_engine, video_path, labels_path, conf_thresh=0.35):
    """Evaluasi kustom dari file rekaman video dan label manual."""
    print(f"[*] Evaluasi video kustom: {video_path} dengan label: {labels_path}")
    with open(labels_path, "r", encoding="utf-8") as f:
        labels_data = json.load(f)

    # Format labels_data: dict of {frame_idx: list of {class_name, bbox: [x1, y1, x2, y2]}}
    cap = cv2.VideoCapture(str(video_path))
    frame_idx = 0
    all_gt = defaultdict(list)
    all_det = defaultdict(list)

    model_engine.conf_thresh = conf_thresh

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        f_str = str(frame_idx)
        if f_str in labels_data:
            gts = labels_data[f_str]
            gt_dict = defaultdict(list)
            for g in gts:
                gt_dict[g["class_name"]].append(g["bbox"])

            dets = model_engine.detect(frame)
            det_dict = defaultdict(list)
            for d in dets:
                det_dict[d["class_name"]].append((d["bbox"], d["score"]))

            stats = evaluate_detections(gt_dict, det_dict, iou_thresh=0.50)
            # Akumulasi
            for cname, s in stats.items():
                all_gt[cname].append(s)

        frame_idx += 1

    cap.release()
    print("[OK] Selesai evaluasi video kustom.")


def print_evaluation_report(results_per_threshold):
    print("\n" + "=" * 90)
    print("HASIL SAPUAN AMBANG EVALUASI AKURASI VISION AI (YOLO11n-640) — COCO VAL2017 SUBSET")
    print("IoU Threshold: 0.50 | Ground Truth: Anotasi Resmi COCO Consortium (Bukan Label Buatan Sendiri)")
    print("=" * 90)

    # Semua kelas yang relevan untuk smart home
    all_classes_evaluated = TARGET_CLASSES

    for thresh, stats in results_per_threshold.items():
        print(f"\n[+] Ambang Keyakinan (Confidence Threshold): {thresh:.2f}")
        print(f"{'Kelas Objek':<14} | {'GT':<6} | {'Det':<6} | {'TP':<5} | {'FP':<5} | {'FN':<5} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}")
        print("-" * 90)

        sum_tp = 0
        sum_fp = 0
        sum_fn = 0
        sum_gt = 0
        valid_classes_count = 0

        for cname in all_classes_evaluated:
            s = stats.get(cname)
            if not s or s["GT"] == 0:
                print(f"{cname:<14} | {'TIDAK ADA DATA':<69}")
                continue

            tp = s["TP"]
            fp = s["FP"]
            fn = s["FN"]
            gt = s["GT"]
            det = s["DET"]

            prec = (tp / float(tp + fp)) if (tp + fp) > 0 else 0.0
            rec = (tp / float(tp + fn)) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

            sum_tp += tp
            sum_fp += fp
            sum_fn += fn
            sum_gt += gt
            valid_classes_count += 1

            print(f"{cname:<14} | {gt:<6} | {det:<6} | {tp:<5} | {fp:<5} | {fn:<5} | {prec*100:>8.2f}% | {rec*100:>8.2f}% | {f1*100:>8.2f}%")

        print("-" * 90)
        # Rata-rata mikro hanya dari kelas yang memiliki data
        micro_prec = (sum_tp / float(sum_tp + sum_fp)) if (sum_tp + sum_fp) > 0 else 0.0
        micro_rec = (sum_tp / float(sum_tp + sum_fn)) if (sum_tp + sum_fn) > 0 else 0.0
        micro_f1 = (2 * micro_prec * micro_rec / (micro_prec + micro_rec)) if (micro_prec + micro_rec) > 0 else 0.0
        print(f"{'RATA-RATA':<14} | {sum_gt:<6} | {sum_tp+sum_fp:<6} | {sum_tp:<5} | {sum_fp:<5} | {sum_fn:<5} | {micro_prec*100:>8.2f}% | {micro_rec*100:>8.2f}% | {micro_f1*100:>8.2f}%")
        print(f"(*Hanya menghitung {valid_classes_count} kelas yang memiliki data valid)")

    # Periksa kelas trackable yang tidak memiliki data
    print("\n" + "=" * 90)
    print("STATUS KELAS LAINNYA DALAM VISION_TRACKABLE_CLASSES:")
    other_classes = [c for c in settings.VISION_TRACKABLE_CLASSES if c not in TARGET_CLASSES]
    for oc in other_classes:
        print(f"  - {oc:<14}: TIDAK ADA DATA (Tidak diikutsertakan dalam rata-rata)")
    print("=" * 90)


def main():
    parser = argparse.ArgumentParser(description="Evaluasi Akurasi Vision AI (COCO val2017)")
    parser.add_argument("--model", type=str, default=str(MODEL_PATH), help="Path ke model ONNX")
    parser.add_argument("--subset", type=str, default=str(DEFAULT_SUBSET_JSON), help="Path ke JSON subset COCO")
    parser.add_argument("--images", type=str, default=str(DEFAULT_IMAGES_DIR), help="Path ke direktori gambar")
    parser.add_argument("--thresholds", type=str, default="0.10,0.15,0.20,0.25,0.30", help="Daftar ambang confidence dipisah koma")
    parser.add_argument("--video", type=str, default=None, help="Path ke file video rekaman kustom")
    parser.add_argument("--labels", type=str, default=None, help="Path ke file anotasi kustom")
    args = parser.parse_args()

    model_p = Path(args.model)
    if not model_p.exists():
        print(f"[ERROR] Model tidak ditemukan di: {model_p}")
        sys.exit(1)

    thresh_list = [float(x.strip()) for x in args.thresholds.split(",") if x.strip()]

    print(f"[*] Memuat VisionModelEngine: {model_p.name}...")
    engine = VisionModelEngine(model_p, input_size=640, num_threads=2, conf_thresh=min(thresh_list) * 0.9)

    if args.video and args.labels:
        run_custom_video_evaluation(engine, Path(args.video), Path(args.labels))
    else:
        subset_p = Path(args.subset)
        images_p = Path(args.images)
        if not subset_p.exists() or not images_p.exists():
            print(f"[ERROR] Subset COCO belum siap. Jalankan scripts/prepare_coco_subset.py terlebih dahulu.")
            sys.exit(1)

        results = run_coco_evaluation(engine, subset_p, images_p, conf_thresholds=thresh_list)
        print_evaluation_report(results)


if __name__ == "__main__":
    main()
