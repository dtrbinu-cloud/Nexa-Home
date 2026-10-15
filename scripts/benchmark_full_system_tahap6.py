#!/usr/bin/env python3
"""
benchmark_full_system_tahap6.py
Benchmark beban penuh sistem Tahap 6:
- 3 KAMERA AKTIF (FFmpeg stream ke MediaMTX RTSP)
- DETEKSI OBJEK AKTIF (YOLO11n ONNX FP32)
- ESTIMASI POSE AKTIF (YOLO11n-pose ONNX FP32)
- PEREKAMAN AKTIF (CameraRecordingSession enkripsi AES-GCM)
Mengukur:
- CPU & RAM per proses: Backend, MediaMTX, AI Worker, Tiap FFmpeg
- FPS inferensi aktual per kamera (jumlah frame yang benar-benar diinferensi per detik per kamera)
"""

import asyncio
import os
from pathlib import Path
import subprocess
import sys
import time

import cv2
import numpy as np
import psutil

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.benchmark_camera_real import ensure_cameras, measure_proc_metrics, run_ffmpeg_synthetic_camera
from server.app.worker.vision_worker import VisionWorker
from server.app.core.family.pose_engine import PoseEngine
from server.app.core.camera.motion_service import CameraRecordingSession
from server.app.core.camera.encryption import save_encrypted_clip

async def main():
    print("=" * 80)
    print("BENCHMARK BEBAN PENUH TAHAP 6: 3 KAMERA + DETEKSI + POSE + PEREKAMAN AKTIF")
    print("=" * 80)

    cam_ids = ["bench_cam_1", "bench_cam_2", "bench_cam_3"]
    ensure_cameras(cam_ids)

    # 1. Deteksi MediaMTX
    mtx_proc = None
    for p in psutil.process_iter(['name', 'cmdline']):
        if 'mediamtx' in (p.info['name'] or '').lower():
            mtx_proc = p
            break
    print(f"[*] MediaMTX PID: {mtx_proc.pid if mtx_proc else 'Tidak ditemukan'}")

    # 2. Jalankan 3 FFmpeg camera publisher
    ffmpeg_subs = []
    ffmpeg_procs = []
    for cid in cam_ids:
        sub = run_ffmpeg_synthetic_camera(cid)
        ffmpeg_subs.append(sub)
        ffmpeg_procs.append(psutil.Process(sub.pid))
        print(f"[*] FFmpeg {cid} PID: {sub.pid}")

    # 3. Inisialisasi Vision Worker dengan Pose Engine
    print("[*] Inisialisasi Vision Worker + YOLO11n-pose + Sesi Perekaman...")
    worker = VisionWorker(worker_id="benchmark_tahap6")
    worker_proc = psutil.Process()

    # Sesi perekaman per kamera
    recording_sessions = {cid: CameraRecordingSession(cid, fps=15) for cid in cam_ids}

    # Cari Backend
    backend_proc = None
    for p in psutil.process_iter(['name', 'cmdline']):
        cmd = " ".join(p.info['cmdline'] or [])
        if "uvicorn" in cmd and "server.app.main:app" in cmd:
            backend_proc = p
            break
    print(f"[*] Backend Uvicorn PID: {backend_proc.pid if backend_proc else 'Tidak ditemukan'}")

    # Warmup 3 detik
    print("[*] Pemanasan sistem (3 detik)...")
    await asyncio.sleep(3)

    # Reset psutil CPU
    worker_proc.cpu_percent(None)
    if mtx_proc: mtx_proc.cpu_percent(None)
    if backend_proc: backend_proc.cpu_percent(None)
    for p in ffmpeg_procs: p.cpu_percent(None)

    duration_sec = 25
    print(f"[*] Mengukur beban kerja selama {duration_sec} detik...")
    start_time = time.time()

    samples_backend_cpu = []
    samples_backend_ram = []
    samples_mtx_cpu = []
    samples_mtx_ram = []
    samples_worker_cpu = []
    samples_worker_ram = []
    samples_ff_cpu = [[] for _ in cam_ids]
    samples_ff_ram = [[] for _ in cam_ids]

    inference_counts = {cid: 0 for cid in cam_ids}
    pose_counts = {cid: 0 for cid in cam_ids}
    recorded_clips = 0
    frame_idx = 0

    # Buat synthetic frame dengan person dan pergerakan
    dummy_frame = np.full((480, 640, 3), 40, dtype=np.uint8)

    while (time.time() - start_time) < duration_sec:
        loop_start = time.perf_counter()
        frame_idx += 1

        for idx, cid in enumerate(cam_ids):
            # Sintesis pergerakan orang
            box_x = int((np.sin(frame_idx * 0.15 + idx) + 1.0) * 0.5 * 300) + 50
            f = dummy_frame.copy()
            # Gambar figur orang sintetis
            cv2.rectangle(f, (box_x, 100), (box_x + 120, 380), (180, 180, 200), -1)
            cv2.circle(f, (box_x + 60, 140), 30, (200, 200, 220), -1)

            # 1. Inferensi Deteksi Objek (YOLO11n)
            detections = worker.model_engine.detect(f)
            inference_counts[cid] += 1

            # 2. Inferensi Pose jika ada orang terdeteksi
            pose_res = worker.pose_engine.estimate_poses(f)
            pose_counts[cid] += 1

            # 3. Perekaman Aktif (feed frame ke CameraRecordingSession)
            clip_res = recording_sessions[cid].push_frame(f, motion_detected=True)
            if clip_res:
                recorded_clips += 1

        # Sampling psutil
        w_cpu, w_ram = measure_proc_metrics(worker_proc)
        samples_worker_cpu.append(w_cpu)
        samples_worker_ram.append(w_ram)

        if mtx_proc:
            m_cpu, m_ram = measure_proc_metrics(mtx_proc)
            samples_mtx_cpu.append(m_cpu)
            samples_mtx_ram.append(m_ram)

        if backend_proc:
            b_cpu, b_ram = measure_proc_metrics(backend_proc)
            samples_backend_cpu.append(b_cpu)
            samples_backend_ram.append(b_ram)

        for i, fp in enumerate(ffmpeg_procs):
            f_cpu, f_ram = measure_proc_metrics(fp)
            samples_ff_cpu[i].append(f_cpu)
            samples_ff_ram[i].append(f_ram)

        elapsed = time.perf_counter() - loop_start
        # Pacing agar frame rate inferensi realistis ~ 1.5 - 2 FPS per kamera
        await asyncio.sleep(max(0.0, 0.4 - elapsed))

    # Hentikan FFmpeg
    for s in ffmpeg_subs:
        try:
            s.terminate()
            s.wait(timeout=1)
        except Exception:
            s.kill()

    total_time = time.time() - start_time
    avg_b_cpu = float(np.mean(samples_backend_cpu)) if samples_backend_cpu else 0.0
    avg_b_ram = float(np.mean(samples_backend_ram)) if samples_backend_ram else 0.0
    avg_m_cpu = float(np.mean(samples_mtx_cpu)) if samples_mtx_cpu else 0.0
    avg_m_ram = float(np.mean(samples_mtx_ram)) if samples_mtx_ram else 0.0
    avg_w_cpu = float(np.mean(samples_worker_cpu)) if samples_worker_cpu else 0.0
    avg_w_ram = float(np.mean(samples_worker_ram)) if samples_worker_ram else 0.0

    avg_ff_cpu = [float(np.mean(samples_ff_cpu[i])) for i in range(len(cam_ids))]
    avg_ff_ram = [float(np.mean(samples_ff_ram[i])) for i in range(len(cam_ids))]

    total_cpu = avg_b_cpu + avg_m_cpu + avg_w_cpu + sum(avg_ff_cpu)
    total_ram = avg_b_ram + avg_m_ram + avg_w_ram + sum(avg_ff_ram)

    print("\n" + "=" * 80)
    print("HASIL PENGUKURAN BEBAN PENUH TAHAP 6 (3 KAMERA + DETEKSI + POSE + PEREKAMAN):")
    print("=" * 80)
    print(f"1. Backend (Uvicorn FastAPI)   : CPU {avg_b_cpu:5.1f}% | RAM {avg_b_ram:6.1f} MB")
    print(f"2. MediaMTX RTSP Server        : CPU {avg_m_cpu:5.1f}% | RAM {avg_m_ram:6.1f} MB")
    print(f"3. Vision Worker (YOLO11+Pose) : CPU {avg_w_cpu:5.1f}% | RAM {avg_w_ram:6.1f} MB")
    for i, cid in enumerate(cam_ids):
        print(f"4.{i+1} FFmpeg Kamera #{i+1} ({cid}) : CPU {avg_ff_cpu[i]:5.1f}% | RAM {avg_ff_ram[i]:6.1f} MB")
    print("-" * 80)
    print(f"TOTAL SELURUH PROSES SISTEM    : CPU {total_cpu:5.1f}% | RAM {total_ram:6.1f} MB")
    print("-" * 80)
    print("FPS INFERENSI AKTUAL PER KAMERA (Frame yang benar-benar diinferensi / detik):")
    for cid in cam_ids:
        det_fps = inference_counts[cid] / total_time
        pose_fps = pose_counts[cid] / total_time
        print(f"  • {cid}: {det_fps:.2f} deteksi FPS | {pose_fps:.2f} pose FPS (Total inferensi: {inference_counts[cid]} deteksi, {pose_counts[cid]} pose dalam {total_time:.1f}s)")
    print(f"Status Perekaman Aktif         : YA ({sum(len(s.recorded_frames) for s in recording_sessions.values())} frame dalam buffer aktif)")
    print(f"Suhu CPU                       : TIDAK DIUKUR (Hardware/OS tidak menyediakan API suhu yang didukung)")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
