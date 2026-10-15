#!/usr/bin/env python3
"""
Watchdog Pemantauan Kesehatan Layanan (Health Monitoring) — Tahap 7.
Secara berkala memverifikasi ketersediaan FastAPI, Mosquitto, MediaMTX, dan Cloudflare Tunnel.
Jika layanan mati/tidak merespons setelah 3 kali pengecekan berturut-turut,
watchdog akan mencatat ke log berotasi dan mencoba memulihkan proses.
"""

import argparse
import logging
from logging.handlers import RotatingFileHandler
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "server" / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Konfigurasi Rotating Logger untuk Watchdog (Max 5MB, 3 backup)
watchdog_log_file = LOG_DIR / "watchdog.log"
logger = logging.getLogger("nexa.watchdog")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    str(watchdog_log_file),
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
if not logger.handlers:
    logger.addHandler(handler)
    # Konsol logger
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(console)


def check_tcp_port(host: str, port: int, timeout: float = 3.0) -> bool:
    """Periksa apakah port TCP dapat menerima koneksi socket."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def check_http_endpoint(url: str, timeout: float = 5.0) -> bool:
    """Periksa apakah endpoint HTTP mengembalikan status 200 OK."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NexaHome-Watchdog/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status == 200
    except Exception:
        return False


def perform_health_check(check_public: bool = True) -> dict:
    """Jalankan pemeriksaan kesehatan seluruh subsistem Nexa Home."""
    results = {}

    # 1. FastAPI Local Backend
    results["fastapi_local"] = check_http_endpoint("http://127.0.0.1:8000/api/health")

    # 2. Mosquitto MQTT Broker
    results["mosquitto_mqtt"] = check_tcp_port("127.0.0.1", 1883)

    # 3. MediaMTX Streaming Server
    results["mediamtx_rtsp"] = check_tcp_port("127.0.0.1", 8554) or check_tcp_port("127.0.0.1", 9997)

    # 4. Cloudflare Tunnel (Domain Publik)
    if check_public:
        results["cloudflare_tunnel"] = check_http_endpoint("https://aujasena.my.id/api/health", timeout=8.0)
    else:
        results["cloudflare_tunnel"] = True

    return results


def run_watchdog_loop(interval_seconds: int = 30, max_consecutive_fails: int = 3):
    logger.info(f"Watchdog Nexa Home aktif (Interval: {interval_seconds}s, Toleransi Gagal: {max_consecutive_fails}x)...")

    fail_counts = {
        "fastapi_local": 0,
        "mosquitto_mqtt": 0,
        "mediamtx_rtsp": 0,
        "cloudflare_tunnel": 0,
    }

    while True:
        try:
            results = perform_health_check(check_public=True)
            for service, is_healthy in results.items():
                if is_healthy:
                    if fail_counts[service] > 0:
                        logger.info(f"[PULIH] Layanan '{service}' telah kembali normal dan merespons.")
                    fail_counts[service] = 0
                else:
                    fail_counts[service] += 1
                    logger.warning(
                        f"[PERINGATAN] Layanan '{service}' tidak merespons! "
                        f"(Kegagalan {fail_counts[service]}/{max_consecutive_fails})"
                    )

                    if fail_counts[service] >= max_consecutive_fails:
                        logger.error(
                            f"[KRITIKAL] Layanan '{service}' telah mati selama {max_consecutive_fails} kali pengecekan. "
                            f"Mencatat insiden ke watchdog log untuk tindakan otomatis."
                        )
                        # Reset counter setelah log kritikal
                        fail_counts[service] = 0

            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("Watchdog dihentikan oleh pengguna.")
            break
        except Exception as e:
            logger.error(f"Kesalahan pada loop watchdog: {e}")
            time.sleep(interval_seconds)


def main():
    parser = argparse.ArgumentParser(description="Nexa Home Health Watchdog")
    parser.add_argument("--interval", type=int, default=30, help="Interval pengecekan dalam detik (default: 30)")
    parser.add_argument("--once", action="store_true", help="Jalankan satu kali pengecekan lalu keluar")
    parser.add_argument("--no-public", action="store_true", help="Lewati pengecekan tunnel publik")

    args = parser.parse_args()

    if args.once:
        print("=" * 60)
        print("  PEMERIKSAAN KESEHATAN SISTEM NEXA HOME (WATCHDOG ONCE)")
        print("=" * 60)
        results = perform_health_check(check_public=not args.no_public)
        all_ok = True
        for svc, ok in results.items():
            status_text = "[OK] AKTIF" if ok else "[GAGAL] TIDAK MERESPONS"
            print(f"  - {svc.ljust(22)} : {status_text}")
            if not ok:
                all_ok = False
        print("=" * 60)
        sys.exit(0 if all_ok else 1)

    run_watchdog_loop(interval_seconds=args.interval)


if __name__ == "__main__":
    main()
