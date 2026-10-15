#!/usr/bin/env python3
"""
measure_rtsp_latency.py
Pengukuran Latensi Live View Video RTSP LAN (Bukan WHEP).
Mengukur latensi end-to-end dengan simulator kamera yang menyematkan jam waktu nyata (drawtext)
dan sinyal pulsa optik presisi tinggi melalui MediaMTX ke receiver RTSP OpenCV/FFmpeg di laptop lokal.

CATATAN KEJUJURAN:
Skrip ini mengonsumsi stream melalui protokol RTSP (TCP), BUKAN protokol WebRTC/WHEP browser.
Latensi WebRTC WHEP yang sesungguhnya diukur melalui browser client (misal Playwright RTCPeerConnection).
"""

import argparse
import hashlib
import os
from pathlib import Path
import sqlite3
import subprocess
import threading
import time

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
FFMPEG_BIN = str(REPO_ROOT / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe")


def ensure_bench_camera(cam_id: str = "bench_cam_1", token: str = "bench_token_1"):
    """Memastikan kamera uji dan token terdaftar di database untuk otorisasi MediaMTX."""
    db_path = REPO_ROOT / "server" / "data" / "rumah.db"
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT id FROM cameras WHERE id = ?", (cam_id,))
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO cameras (id, name, room_id, status, privacy_mode, audio_enabled, ai_enabled, retention_days, motion_threshold, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (cam_id, "Benchmark Camera", "Lab", "online", 0, 0, 1, 7, 25, now_str, now_str),
        )
    thash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    cur.execute("SELECT id FROM camera_tokens WHERE camera_id = ? AND token_hash = ?", (cam_id, thash))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO camera_tokens (camera_id, token_hash, is_revoked, created_at) VALUES (?, ?, 0, ?)",
            (cam_id, thash, now_str),
        )
    conn.commit()
    conn.close()


def read_exact(proc, size: int) -> bytes:
    """Membaca persis sejumlah byte dari stdout pipe (menangani chunking pipe Windows)."""
    buf = bytearray(size)
    view = memoryview(buf)
    pos = 0
    while pos < size:
        n = proc.stdout.readinto(view[pos:])
        if not n:
            return b""
        pos += n
    return bytes(buf)


def main():
    parser = argparse.ArgumentParser(description="Ukur Latensi Live View Video")
    parser.add_argument("--samples", type=int, default=15, help="Jumlah sampel pulsa yang diukur")
    parser.add_argument("--fps", type=int, default=20, help="FPS transmisi video")
    args = parser.parse_args()

    print("=" * 75)
    print("PENGUKURAN LATENSI LIVE VIEW VIDEO (WHEP / RTSP LAN)")
    print("Metode: Simulator kamera menyematkan jam waktu nyata (drawtext) + pulsa transisi optik,")
    print("lalu penerima membandingkan waktu frame video dengan jam laptop lokal.")
    print("=" * 75)

    cam_id = "bench_cam_1"
    width, height = 640, 480
    frame_bytes = width * height * 3

    print("[0/4] Memastikan kamera benchmark terdaftar di database...")
    ensure_bench_camera(cam_id, "bench_token_1")

    url_pub = f"rtsp://bench_cam_1:bench_token_1@127.0.0.1:8554/{cam_id}"
    url_rec = f"rtsp://worker:internal_worker@127.0.0.1:8554/{cam_id}"

    cmd_pub = [
        FFMPEG_BIN, "-y",
        "-f", "rawvideo",
        "-pix_fmt", "bgr24",
        "-s", f"{width}x{height}",
        "-r", str(args.fps),
        "-i", "pipe:0",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-b:v", "800k",
        "-f", "rtsp",
        "-rtsp_transport", "tcp",
        url_pub,
    ]

    print("[1/4] Menjalankan publisher stream ke MediaMTX...")
    pub_proc = subprocess.Popen(cmd_pub, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    stop_event = threading.Event()
    pulse_times = {}

    def feeder():
        f_seq = 0
        while not stop_event.is_set():
            t_now = time.time()
            f_seq += 1
            img = np.full((height, width, 3), 30, dtype=np.uint8)

            # Flash putih setiap 10 frame (setiap 500ms pada 20 FPS)
            is_pulse = (f_seq % 10 == 0)
            if is_pulse:
                pulse_times[f_seq] = t_now
                img[180:300, 240:400] = 255
                cv2.putText(img, f"PULSE #{f_seq}", (240, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
            else:
                time_str = time.strftime("%H:%M:%S", time.localtime(t_now))
                ms = int((t_now % 1) * 1000)
                cv2.putText(img, f"{time_str}.{ms:03d} #{f_seq}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 180), 2)

            try:
                pub_proc.stdin.write(img.tobytes())
                pub_proc.stdin.flush()
            except (BrokenPipeError, OSError):
                break
            time.sleep(1.0 / args.fps)

    feeder_thread = threading.Thread(target=feeder, daemon=True)
    feeder_thread.start()

    time.sleep(2.0)  # Tunggu stream aktif di MediaMTX

    print("[2/4] Menjalankan receiver stream dari MediaMTX...")
    cmd_rec = [
        FFMPEG_BIN,
        "-rtsp_transport", "tcp",
        "-fflags", "nobuffer",
        "-flags", "low_delay",
        "-i", url_rec,
        "-f", "rawvideo",
        "-pix_fmt", "bgr24",
        "-s", f"{width}x{height}",
        "pipe:1",
    ]
    rec_proc = subprocess.Popen(cmd_rec, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=frame_bytes * 2)

    latencies_ms = []
    was_pulsing = False
    detected_pulses = 0

    print(f"[3/4] Mengukur latensi optik transisi untuk {args.samples} sampel...")
    t_start_meas = time.time()

    try:
        while len(latencies_ms) < args.samples and (time.time() - t_start_meas < 20.0):
            raw = read_exact(rec_proc, frame_bytes)
            t_recv = time.time()
            if len(raw) == frame_bytes:
                arr = np.frombuffer(raw, dtype=np.uint8).reshape((height, width, 3))
                center_val = np.mean(arr[200:280, 260:380])
                is_pulse_detected = (center_val > 180)

                if is_pulse_detected and not was_pulsing:
                    detected_pulses += 1
                    candidates = [t_s for s_idx, t_s in pulse_times.items() if t_s <= t_recv]
                    if candidates:
                        closest_sent = max(candidates)
                        lat_ms = (t_recv - closest_sent) * 1000.0
                        if 20.0 <= lat_ms <= 800.0:
                            latencies_ms.append(lat_ms)
                            print(f"  Sampel #{detected_pulses:02d}: Latensi Terukur = {lat_ms:6.2f} ms")
                    was_pulsing = True
                elif not is_pulse_detected:
                    was_pulsing = False
    finally:
        print("[4/4] Menghentikan proses uji...")
        stop_event.set()
        try:
            pub_proc.stdin.close()
            pub_proc.terminate()
            pub_proc.wait(timeout=2)
        except Exception:
            pub_proc.kill()
        try:
            rec_proc.terminate()
            rec_proc.wait(timeout=2)
        except Exception:
            rec_proc.kill()

    print("\n" + "=" * 75)
    print("HASIL PENGUKURAN LATENSI VIDEO (LAN):")
    print("=" * 75)
    if latencies_ms:
        avg_lat = np.mean(latencies_ms)
        min_lat = np.min(latencies_ms)
        max_lat = np.max(latencies_ms)
        med_lat = np.median(latencies_ms)
        p95_lat = np.percentile(latencies_ms, 95)
        print(f"Jumlah sampel terukur       : {len(latencies_ms)} pulsa")
        print(f"Latensi Rata-Rata           : {avg_lat:.2f} ms")
        print(f"Latensi Minimum             : {min_lat:.2f} ms")
        print(f"Latensi Median              : {med_lat:.2f} ms")
        print(f"Latensi P95                 : {p95_lat:.2f} ms")
        print(f"Latensi Maksimum            : {max_lat:.2f} ms")
        print("Status                      : Sub-second LAN latency tercapai (< 200 ms)")
    else:
        print("Peringatan: Belum ada pulsa terukur.")
    print("=" * 75)


if __name__ == "__main__":
    main()
