#!/usr/bin/env python3
"""
benchmark_models.py
Membandingkan model YOLO11 (n vs s, FP32 vs INT8, 480 vs 640) pada mesin lokal.
Mengukur:
- Latensi inferensi (ms)
- FPS per kamera dan kapasitas 3 kamera (FPS / 3)
- CPU (%) via psutil (dibatasi 2 thread ONNX Runtime)
- RAM (MB) via psutil
Memastikan tidak ada angka perkiraan (Aturan Kejujuran).
"""

import sys
import time
from pathlib import Path
import numpy as np
import onnxruntime as ort
import psutil

REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = REPO_ROOT / "server" / "data" / "models" / "yolo"

VARIANTS = [
    # (name, file_name, input_size, model_type, precision)
    ("YOLO11n-480-FP32", "yolo11n_480.onnx", 480, "n", "FP32"),
    ("YOLO11n-480-INT8", "yolo11n_480_int8.onnx", 480, "n", "INT8"),
    ("YOLO11n-640-FP32", "yolo11n_640.onnx", 640, "n", "FP32"),
    ("YOLO11n-640-INT8", "yolo11n_640_int8.onnx", 640, "n", "INT8"),
    ("YOLO11s-480-FP32", "yolo11s_480.onnx", 480, "s", "FP32"),
    ("YOLO11s-480-INT8", "yolo11s_480_int8.onnx", 480, "s", "INT8"),
    ("YOLO11s-640-FP32", "yolo11s_640.onnx", 640, "s", "FP32"),
    ("YOLO11s-640-INT8", "yolo11s_640_int8.onnx", 640, "s", "INT8"),
]


def benchmark_variant(name: str, file_name: str, img_sz: int, num_warmup: int = 20, num_runs: int = 50):
    model_path = MODELS_DIR / file_name
    if not model_path.exists():
        return {
            "name": name,
            "status": "NOT_FOUND",
            "error": f"File {file_name} tidak ditemukan",
        }

    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 2
    opts.inter_op_num_threads = 1
    opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    proc = psutil.Process()
    # Baseline RAM
    base_ram = proc.memory_info().rss / (1024 * 1024)

    t0_load = time.perf_counter()
    session = ort.InferenceSession(str(model_path), sess_options=opts, providers=["CPUExecutionProvider"])
    load_time_ms = (time.perf_counter() - t0_load) * 1000

    input_name = session.get_inputs()[0].name
    # Generate realistic dummy batch
    dummy_input = np.random.uniform(0.0, 1.0, (1, 3, img_sz, img_sz)).astype(np.float32)

    # Warmup
    for _ in range(num_warmup):
        session.run(None, {input_name: dummy_input})

    # Benchmark loop
    latencies = []
    cpu_samples = []
    proc.cpu_percent(interval=None)

    for i in range(num_runs):
        t0 = time.perf_counter()
        session.run(None, {input_name: dummy_input})
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)
        if i % 10 == 0:
            cpu_samples.append(proc.cpu_percent(interval=None))

    avg_ms = float(np.mean(latencies))
    std_ms = float(np.std(latencies))
    p95_ms = float(np.percentile(latencies, 95))
    fps = 1000.0 / avg_ms if avg_ms > 0 else 0.0
    fps_3cam = fps / 3.0  # Kapasitas per kamera jika 3 kamera berbagi 1 worker secara sekuensial

    current_ram = proc.memory_info().rss / (1024 * 1024)
    ram_mb = current_ram
    avg_cpu = float(np.mean(cpu_samples)) if cpu_samples else proc.cpu_percent(interval=None)

    file_size_mb = model_path.stat().st_size / (1024 * 1024)

    return {
        "name": name,
        "status": "OK",
        "file_size_mb": file_size_mb,
        "avg_ms": avg_ms,
        "std_ms": std_ms,
        "p95_ms": p95_ms,
        "fps": fps,
        "fps_3cam": fps_3cam,
        "avg_cpu": avg_cpu,
        "ram_mb": ram_mb,
        "meets_threshold": fps_3cam >= 2.0,  # Syarat: >= 2 FPS per kamera pada beban 3 kamera
    }


def main():
    print("=" * 80)
    print("BENCHMARK MODEL ONNX RUNTIME PADA CPU HOST (THREAD LIMIT = 2)")
    print(f"CPU: {psutil.cpu_count(logical=False)} cores physical, {psutil.cpu_count(logical=True)} logical")
    print("=" * 80)

    results = []
    for name, file_name, img_sz, m_type, prec in VARIANTS:
        print(f"[*] Menguji {name} ({file_name})...", flush=True)
        res = benchmark_variant(name, file_name, img_sz)
        results.append(res)
        if res.get("status") == "OK":
            print(
                f"    -> Latensi: {res['avg_ms']:.2f} ms | FPS: {res['fps']:.2f} | 3-Cam FPS/cam: {res['fps_3cam']:.2f} | RAM: {res['ram_mb']:.1f} MB | CPU: {res['avg_cpu']:.1f}%"
            )
        else:
            print(f"    -> ERROR: {res.get('error')}")

    print("\n" + "=" * 90)
    print(f"{'Varian':<18} | {'Ukuran (MB)':<11} | {'Latensi (ms)':<12} | {'FPS Total':<10} | {'3-Cam FPS/cam':<13} | {'RAM (MB)':<9} | {'>=2 FPS (3 cam)?'}")
    print("-" * 90)
    best_candidate = None
    for r in results:
        if r["status"] != "OK":
            continue
        valid_mark = "YA (MEMENUHI)" if r["meets_threshold"] else "TIDAK (LAMBAT)"
        print(
            f"{r['name']:<18} | {r['file_size_mb']:>9.2f} MB | {r['avg_ms']:>10.2f} ms | {r['fps']:>9.2f} | {r['fps_3cam']:>12.2f} | {r['ram_mb']:>7.1f} MB | {valid_mark}"
        )
    print("=" * 90)


if __name__ == "__main__":
    main()
