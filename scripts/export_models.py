"""
Skrip Ekspor Model YOLO11 ke ONNX (Tahap 5).
- Mengekspor model YOLO11n (deteksi benda COCO) dan YOLO11n-pose (deteksi orang + pose).
- Mendukung ekspor model nano (n) dan small (s), resolusi masukan 480 dan 640.
- Menghasilkan varian FP32 dan INT8 (kuantisasi dinamis ONNX Runtime).
- Menghitung checksum SHA-256 lokal untuk verifikasi integritas.
- Aplikasi runtime berjalan murni menggunakan onnxruntime tanpa dependensi ultralytics.
"""

import argparse
import hashlib
import os
from pathlib import Path
import sys
import time

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

MODEL_DIR = REPO_ROOT / "server" / "data" / "models" / "yolo"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def calculate_sha256(file_path: Path) -> str:
    """Menghitung SHA-256 lokal dari berkas model."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            sha.update(chunk)
    return sha.hexdigest()


def export_yolo_model(model_name: str, imgsz: int = 640) -> Path:
    """Mengekspor model PyTorch Ultralytics ke ONNX format."""
    from ultralytics import YOLO

    print(f"\n[+] Mengekspor {model_name} dengan resolusi {imgsz}x{imgsz}...")
    model = YOLO(f"{model_name}.pt")
    
    # Ekspor ke ONNX
    onnx_path_str = model.export(
        format="onnx",
        imgsz=imgsz,
        dynamic=False,
        simplify=True,
        opset=12,
    )
    src_path = Path(onnx_path_str)
    dst_name = f"{model_name}_{imgsz}.onnx"
    dst_path = MODEL_DIR / dst_name

    # Pindahkan ke folder model
    if src_path != dst_path:
        import shutil
        shutil.copy2(src_path, dst_path)

    size_mb = dst_path.stat().st_size / (1024 * 1024)
    hash_val = calculate_sha256(dst_path)
    print(f"    Berhasil: {dst_path.name} ({size_mb:.2f} MB)")
    print(f"    SHA-256 (dihitung lokal): {hash_val}")
    return dst_path


def quantize_to_int8(onnx_path: Path) -> Path:
    """Melakukan kuantisasi dinamis INT8 pada model ONNX menggunakan ONNX Runtime."""
    import onnxruntime
    from onnxruntime.quantization import quantize_dynamic, QuantType

    int8_name = onnx_path.stem + "_int8.onnx"
    int8_path = onnx_path.parent / int8_name

    print(f"[+] Melakukan kuantisasi dinamis INT8: {onnx_path.name} -> {int8_path.name}...")
    quantize_dynamic(
        model_input=str(onnx_path),
        model_output=str(int8_path),
        weight_type=QuantType.QUInt8,
    )

    size_mb = int8_path.stat().st_size / (1024 * 1024)
    hash_val = calculate_sha256(int8_path)
    print(f"    Berhasil INT8: {int8_path.name} ({size_mb:.2f} MB)")
    print(f"    SHA-256 (dihitung lokal): {hash_val}")
    return int8_path


def main():
    parser = argparse.ArgumentParser(description="Ekspor Model YOLO11 ke ONNX")
    parser.add_argument("--all-variants", action="store_true", help="Ekspor semua varian (n, s, 480, 640, int8)")
    args = parser.parse_args()

    print("=" * 70)
    print("SKRIP EKSPOR MODEL VISION AI RUMAH (YOLO11 -> ONNX)")
    print("Catatan Lisensi: Ultralytics berlisensi AGPL-3.0 (aman pemakaian pribadi).")
    print("=" * 70)

    # 1. Model Wajib Inti (YOLO11n dan YOLO11n-pose @ 640px)
    n_640 = export_yolo_model("yolo11n", imgsz=640)
    pose_640 = export_yolo_model("yolo11n-pose", imgsz=640)

    # Kuantisasi int8 untuk model nano
    n_640_int8 = quantize_to_int8(n_640)

    # Salin default ke server/data/models/yolo/yolo11n.onnx & yolo11n-pose.onnx
    import shutil
    shutil.copy2(n_640, MODEL_DIR / "yolo11n.onnx")
    shutil.copy2(pose_640, MODEL_DIR / "yolo11n-pose.onnx")
    print(f"\n[OK] Model default disalin ke:")
    print(f"  - {MODEL_DIR / 'yolo11n.onnx'}")
    print(f"  - {MODEL_DIR / 'yolo11n-pose.onnx'}")

    # 2. Varian Perbandingan jika diminta (--all-variants)
    if args.all_variants:
        print("\n--- Mengekspor varian resolusi 480px dan model Small (s) untuk benchmark ---")
        n_480 = export_yolo_model("yolo11n", imgsz=480)
        n_480_int8 = quantize_to_int8(n_480)

        s_640 = export_yolo_model("yolo11s", imgsz=640)
        s_640_int8 = quantize_to_int8(s_640)

        s_480 = export_yolo_model("yolo11s", imgsz=480)
        s_480_int8 = quantize_to_int8(s_480)

    print("\n" + "=" * 70)
    print("EKSPOR SELESAI DENGAN SUKSES.")
    print("=" * 70)


if __name__ == "__main__":
    main()
