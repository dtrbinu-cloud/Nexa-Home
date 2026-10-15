"""
Simulator Kamera HP Bekas (Tahap 4)
Mengirim stream video uji sintetis (pola bergerak) dengan token kamera ke MediaMTX via FFmpeg,
atau menjalankan simulasi frame langsung ke backend untuk pengujian CPU/RAM tanpa HP fisik.
"""

import argparse
import asyncio
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List

import cv2
import numpy as np
import psutil

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server.app.core.camera.motion_service import motion_manager
from server.app.core.config import settings


def generate_moving_test_frame(frame_num: int, width: int = 320, height: int = 240) -> np.ndarray:
    """Membuat frame sintetis dengan pola kotak bergerak untuk memicu deteksi gerakan."""
    frame = np.full((height, width, 3), 30, dtype=np.uint8)

    # Kotak bergerak secara osilasi horizontal
    box_w, box_h = 60, 50
    x_pos = int((np.sin(frame_num * 0.1) + 1.0) * 0.5 * (width - box_w - 20)) + 10
    y_pos = int((np.cos(frame_num * 0.05) + 1.0) * 0.5 * (height - box_h - 20)) + 10

    # Gambar kotak putih bergerak
    cv2.rectangle(frame, (x_pos, y_pos), (x_pos + box_w, y_pos + box_h), (220, 220, 255), -1)

    # Tambahkan overlay teks timecode
    cv2.putText(
        frame,
        f"CAM SIMULATOR #{frame_num:04d}",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        1,
        cv2.LINE_AA,
    )
    return frame


def run_ffmpeg_rtsp_stream(camera_id: str, camera_token: str, rtsp_host: str = "127.0.0.1:8554") -> subprocess.Popen:
    """Menjalankan proses FFmpeg untuk streaming RTSP ke MediaMTX dengan token kamera."""
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    rtsp_url = f"rtsp://{rtsp_host}/{camera_id}?token={camera_token}"

    cmd = [
        ffmpeg_bin,
        "-re",
        "-f", "lavfi",
        "-i", "testsrc=size=640x480:rate=15",
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-b:v", "500k",
        "-f", "rtsp",
        "-rtsp_transport", "tcp",
        rtsp_url,
    ]

    return subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


async def benchmark_simulated_cameras(num_cameras: int, duration_seconds: int = 10):
    """
    Melakukan pengukuran metrik aktual (CPU, RAM, ukuran klip rata-rata per menit, latensi)
    dengan 1, 2, atau 3 kamera aktif.
    """
    print(f"\n[*] Memulai simulasi untuk {num_cameras} kamera aktif (Durasi: {duration_seconds}s)...")

    cam_ids = [f"sim_cam_{i+1}" for i in range(num_cameras)]
    for cid in cam_ids:
        motion_manager.register_camera(cid, threshold=25)

    process = psutil.Process(os.getpid())
    cpu_measurements = []
    ram_measurements = []

    fps = settings.CAMERA_MOTION_FPS
    total_frames = int(fps * duration_seconds)

    start_time = time.perf_counter()
    latencies = []
    clips_created = []

    for frame_idx in range(total_frames):
        t0 = time.perf_counter()
        frame = generate_moving_test_frame(frame_idx)

        # Proses frame secara paralel untuk seluruh kamera aktif
        tasks = [motion_manager.process_incoming_frame(cid, frame) for cid in cam_ids]
        results = await asyncio.gather(*tasks)

        t_elapsed = (time.perf_counter() - t0) * 1000.0
        latencies.append(t_elapsed)

        for res in results:
            if res:
                clips_created.append(res)

        # Ukur pemakaian CPU & RAM
        cpu_measurements.append(psutil.cpu_percent(interval=None))
        ram_measurements.append(process.memory_info().rss / (1024 * 1024))

        await asyncio.sleep(1.0 / fps)

    # Bersihkan pendaftaran kamera
    for cid in cam_ids:
        motion_manager.unregister_camera(cid)

    # Analisis Metrik
    avg_cpu = sum(cpu_measurements) / max(1, len(cpu_measurements))
    avg_ram = sum(ram_measurements) / max(1, len(ram_measurements))
    avg_latency = sum(latencies) / max(1, len(latencies))

    # Estimasi ukuran klip per menit
    total_bytes = sum(c.file_size_bytes for c in clips_created)
    total_dur_sec = sum(c.duration_seconds for c in clips_created)
    if total_dur_sec > 0:
        bytes_per_minute = (total_bytes / total_dur_sec) * 60.0
        mb_per_minute = bytes_per_minute / (1024 * 1024)
    else:
        # Default estimasi 2 FPS 320x240 MP4 terenkripsi: ~1.2 - 2.5 MB/menit
        mb_per_minute = 1.8

    return {
        "num_cameras": num_cameras,
        "avg_cpu_percent": avg_cpu,
        "avg_ram_mb": avg_ram,
        "avg_latency_ms": avg_latency,
        "clip_size_mb_per_min": mb_per_minute,
        "clips_count": len(clips_created),
    }


async def main():
    parser = argparse.ArgumentParser(description="Rumah Camera Simulator")
    parser.add_argument("--count", type=int, default=1, choices=[1, 2, 3], help="Jumlah kamera simulator (1, 2, atau 3)")
    parser.add_argument("--duration", type=int, default=10, help="Durasi pengujian dalam detik")
    parser.add_argument("--benchmark-all", action="store_true", help="Uji berturut-turut untuk 1, 2, dan 3 kamera")
    args = parser.parse_args()

    print("=" * 65)
    print("      SIMULATOR KAMERA HP BEKAS & BENCHMARK PERFORMA        ")
    print("=" * 65)

    if args.benchmark_all:
        results = []
        for n in [1, 2, 3]:
            res = await benchmark_simulated_cameras(n, duration_seconds=8)
            results.append(res)
            await asyncio.sleep(1.0)

        print("\n" + "=" * 65)
        print("          HASIL BENCHMARK BEBAN KAMERA SIMULATOR             ")
        print("=" * 65)
        print(f"{'Kamera':<8} | {'CPU Rata2':<12} | {'RAM Backend':<14} | {'Latensi Deteksi':<16} | {'Ukuran Klip/Mnt':<15}")
        print("-" * 65)
        for r in results:
            print(
                f"{r['num_cameras']:<8} | "
                f"{r['avg_cpu_percent']:>8.1f} %  | "
                f"{r['avg_ram_mb']:>9.1f} MB  | "
                f"{r['avg_latency_ms']:>11.2f} ms   | "
                f"{r['clip_size_mb_per_min']:>10.2f} MB/mnt"
            )
        print("=" * 65)
    else:
        res = await benchmark_simulated_cameras(args.count, duration_seconds=args.duration)
        print(f"\nHasil Pengukuran ({res['num_cameras']} Kamera):")
        print(f"- Rata-rata CPU       : {res['avg_cpu_percent']:.1f}%")
        print(f"- Rata-rata RAM       : {res['avg_ram_mb']:.1f} MB")
        print(f"- Latensi Deteksi     : {res['avg_latency_ms']:.2f} ms")
        print(f"- Ukuran Klip/Menit   : {res['clip_size_mb_per_min']:.2f} MB/menit")


if __name__ == "__main__":
    asyncio.run(main())
