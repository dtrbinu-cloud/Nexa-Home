"""
Skrip Pengukuran Ulang Waktu Sintesis TTS Offline (Piper Asli)
Mengukur 5 kalimat unik berbeda tanpa cache audio menggunakan model neural ONNX nyata.
"""

import asyncio
from pathlib import Path
import sys
import time

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from server.app.core.tts.piper import PiperTTSProvider

# Sumber Resmi Model Suara Piper Bahasa Indonesia (id_ID):
# - Repositori: rhasspy/piper-voices (Hugging Face)
# - Nama Voice Resmi: id_ID-news_tts-medium
# - Path: id/id_ID/news_tts/medium/
# - URL Model ONNX:
#   https://huggingface.co/rhasspy/piper-voices/resolve/main/id/id_ID/news_tts/medium/id_ID-news_tts-medium.onnx
# - URL Config JSON:
#   https://huggingface.co/rhasspy/piper-voices/raw/main/id/id_ID/news_tts/medium/id_ID-news_tts-medium.onnx.json
# - Checksum SHA-256 (dihitung lokal):
#   ONNX : ed8f02aa593f7af6b19acbdb8142e0da0dd72f46194eb33d38e0eb10a52597e8
#   JSON : 1ef677072668a5e172e0759b1d3871f129009d1167f093325a17607f7add5ad7

SAMPLE_SENTENCES = [
    "Sistem pintar Rumah berhasil mendeteksi perintah suara Anda.",
    "Lampu ruang tamu dan pendingin udara kamar utama telah dimatikan.",
    "Suhu ruangan saat ini tercatat dua puluh lima derajat Celsius.",
    "Peringatan keamanan terdeteksi gerakan di area pintu depan rumah.",
    "Semua pintu dan jendela rumah berada dalam kondisi terkunci rapat.",
]


async def run_benchmark():
    provider = PiperTTSProvider()
    if not provider.is_available():
        print("[GAGAL] Piper TTS offline tidak tersedia di host ini.")
        return

    print("=" * 70)
    print("PENGUKURAN WAKTU SINTESIS TTS OFFLINE (PIPER ENGINE ASLI)")
    print("=" * 70)
    print(f"Path Model ONNX : {provider.model_path}")
    print(f"Path Config     : {provider.config_path}")
    print("Engine          : Piper Neural Vocoder (ONNX Runtime CPU)")
    print("=" * 70)

    # Warmup 1 run agar model ONNX ter-load ke RAM
    print("[*] Melakukan inisialisasi / warmup model ONNX...")
    t_init = time.perf_counter()
    _ = await provider.synthesize("Inisialisasi sistem.")
    init_ms = (time.perf_counter() - t_init) * 1000.0
    print(f"[*] Inisialisasi selesai dalam {init_ms:.2f} ms\n")

    durations = []
    for idx, text in enumerate(SAMPLE_SENTENCES, 1):
        t0 = time.perf_counter()
        audio_bytes, mime = await provider.synthesize(text)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        durations.append(elapsed_ms)
        print(f"Kalimat #{idx}: \"{text[:45]}...\"")
        print(f"  -> Durasi: {elapsed_ms:.2f} ms | Ukuran audio: {len(audio_bytes)} bytes | MIME: {mime}")

    avg_ms = sum(durations) / len(durations)
    print("-" * 70)
    print(f"Rata-rata Waktu Sintesis (5 kalimat): {avg_ms:.2f} ms")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_benchmark())
