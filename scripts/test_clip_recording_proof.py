import asyncio
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import cv2

from server.app.core.config import settings
from server.app.core.camera.motion_service import MotionManager
from server.app.core.camera.encryption import decrypt_bytes, get_encryption_key
from server.app.core.database import async_session_factory, Base, engine
import server.app.models.camera # Ensure models registered

async def run_test():
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    manager = MotionManager()
    cam_id = "test_cam_hd"
    fps = 15
    w, h = 1280, 720

    manager.register_camera(cam_id, threshold=20, min_area=500, fps=fps)

    print(f"[*] Menyiapkan simulator stream {w}x{h} @ {fps} FPS...")
    
    # Generate background and moving frames
    base_frame = np.full((h, w, 3), 40, dtype=np.uint8)
    # Add some static texture
    cv2.putText(base_frame, "LIVING ROOM HD 720P", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (200, 200, 200), 2)

    completed_clip = None

    # 1. Pre-roll frames (2 seconds = 30 frames)
    print("[*] Mengirim 30 frame pre-roll (tanpa gerakan)...")
    for i in range(30):
        frame = base_frame.copy()
        res = await manager.process_incoming_frame(cam_id, frame)
        if res:
            completed_clip = res

    # 2. Motion frames (30 frames with a moving white box)
    print("[*] Mengirim 30 frame dengan gerakan aktif...")
    for i in range(30):
        frame = base_frame.copy()
        box_x = 200 + i * 15
        cv2.rectangle(frame, (box_x, 300), (box_x + 150, 450), (255, 255, 255), -1)
        res = await manager.process_incoming_frame(cam_id, frame)
        if res:
            completed_clip = res

    # 3. Post-roll frames (45 frames without motion)
    print("[*] Mengirim 45 frame pasca-gerakan (post-roll)...")
    for i in range(45):
        frame = base_frame.copy()
        res = await manager.process_incoming_frame(cam_id, frame)
        if res:
            completed_clip = res
            break

    if not completed_clip:
        print("[!] Klip belum selesai, memanggil force push...")
        session = manager.active_sessions.get(cam_id)
        if session and session.is_recording:
            clip_data = session._finalize_clip()
            if clip_data:
                completed_clip = await manager._save_clip_to_storage_and_db(clip_data)

    assert completed_clip is not None, "Klip rekaman gagal dibuat!"
    print(f"[+] Klip berhasil disimpan ke storage: {completed_clip.file_path}")
    print(f"    ID Klip: {completed_clip.id}")
    print(f"    Durasi: {completed_clip.duration_seconds:.2f} detik")
    print(f"    Ukuran file terenkripsi (.enc): {completed_clip.file_size_bytes} bytes")

    # Dekripsi klip untuk validasi ffprobe
    enc_path = Path(completed_clip.file_path)
    enc_bytes = enc_path.read_bytes()
    decrypted_mp4_bytes = decrypt_bytes(enc_bytes, completed_clip.nonce, completed_clip.camera_id)

    temp_decrypted = Path("scripts/test_clip_decrypted_1280x720.mp4")
    temp_decrypted.write_bytes(decrypted_mp4_bytes)

    ffprobe_bin = shutil.which("ffprobe") or "ffprobe"
    cmd = [
        ffprobe_bin,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height,r_frame_rate,avg_frame_rate,bit_rate,duration,nb_frames",
        "-show_entries", "format=duration,size,bit_rate",
        "-of", "json",
        str(temp_decrypted)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print("\n" + "=" * 60)
    print("KELUARAN MENTAH FFPROBE PADA KLIP HASIL DEKRIPSI:")
    print("=" * 60)
    print(res.stdout)

    data = json.loads(res.stdout)
    stream = data.get("streams", [{}])[0]
    fmt = data.get("format", {})

    codec = stream.get("codec_name")
    width = stream.get("width")
    height = stream.get("height")
    fps_eval = eval(stream.get("r_frame_rate", "15/1"))
    total_size = int(fmt.get("size", len(decrypted_mp4_bytes)))
    duration = float(fmt.get("duration", completed_clip.duration_seconds))
    bitrate = int(fmt.get("bit_rate", 0))

    bytes_per_sec = total_size / duration if duration > 0 else 0
    mb_per_min = (bytes_per_sec * 60) / (1024 * 1024)

    print("=" * 60)
    print("HASIL ANALISIS REKAMAN:")
    print(f"  Codec        : {codec}")
    print(f"  Resolusi     : {width}x{height}")
    print(f"  FPS          : {fps_eval:.2f}")
    print(f"  Durasi       : {duration:.2f} detik")
    print(f"  Bitrate      : {bitrate} bps ({bitrate / 1000:.1f} kbps)")
    print(f"  Ukuran File  : {total_size} bytes ({total_size / 1024:.2f} KB)")
    print(f"  Ukuran / Menit: {mb_per_min:.2f} MB / menit")
    print("=" * 60)

    # Clean up decrypted temp file
    temp_decrypted.unlink(missing_ok=True)

if __name__ == "__main__":
    asyncio.run(run_test())
