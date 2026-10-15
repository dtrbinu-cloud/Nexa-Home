#!/usr/bin/env python3
"""
scripts/download_coco_annotations.py — Mengunduh instances_val2017.json resmi
"""
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET_FILE = REPO_ROOT / "tests" / "data" / "instances_val2017.json"
URL = "https://huggingface.co/datasets/merve/coco/resolve/main/annotations/instances_val2017.json"

def main():
    TARGET_FILE.parent.mkdir(parents=True, exist_ok=True)
    if TARGET_FILE.exists() and TARGET_FILE.stat().st_size > 19_000_000:
        print(f"[OK] instances_val2017.json sudah ada ({TARGET_FILE.stat().st_size} bytes).")
        return

    print(f"[*] Mengunduh {URL}...")
    t0 = time.time()
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, open(TARGET_FILE, "wb") as out:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            downloaded += len(chunk)
            print(f"\rUnduh: {downloaded / 1024 / 1024:.1f} MB / {total / 1024 / 1024:.1f} MB", end="", flush=True)

    dt = time.time() - t0
    print(f"\n[OK] Selesai dalam {dt:.1f} detik ({TARGET_FILE.stat().st_size} bytes).")

if __name__ == "__main__":
    main()
