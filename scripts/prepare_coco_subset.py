#!/usr/bin/env python3
"""
scripts/prepare_coco_subset.py
Mengambil subset evaluasi COCO val2017 resmi (minimal 30 gambar/objek per kelas).
Kelas: cell phone, remote, bottle, cup, laptop, book, backpack, handbag, person.
Aturan:
- person: hanya gambar yang SEMUA orangnya teranotasi (tanpa iscrowd=1).
- Gambar diunduh otomatis dari http://images.cocodataset.org/val2017/<id>.jpg
- Gambar disimpan di tests/data/coco_val2017_subset/ (diabaikan oleh git).
- Metadata anotasi subset disimpan di tests/data/coco_eval_subset.json.
"""

import asyncio
from collections import defaultdict
import json
from pathlib import Path
import time
import urllib.request
import aiohttp

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTANCES_JSON = REPO_ROOT / "tests" / "data" / "instances_val2017.json"
OUTPUT_DIR = REPO_ROOT / "tests" / "data" / "coco_val2017_subset"
SUBSET_JSON = REPO_ROOT / "tests" / "data" / "coco_eval_subset.json"

TARGET_CLASSES = [
    "cell phone",
    "remote",
    "bottle",
    "cup",
    "laptop",
    "book",
    "backpack",
    "handbag",
    "person",
]
MIN_IMAGES_PER_CLASS = 35


async def download_image(session: aiohttp.ClientSession, img_id: int, target_path: Path):
    if target_path.exists() and target_path.stat().st_size > 1000:
        return
    url = f"http://images.cocodataset.org/val2017/{img_id:012d}.jpg"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                data = await resp.read()
                target_path.write_bytes(data)
            else:
                print(f"[!] Gagal unduh {url}: status {resp.status}")
    except Exception as e:
        print(f"[!] Error unduh {url}: {e}")


async def main():
    if not INSTANCES_JSON.exists():
        print(f"[ERROR] {INSTANCES_JSON} tidak ditemukan. Jalankan download_coco_annotations.py terlebih dahulu.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("[*] Membaca instances_val2017.json...")
    with open(INSTANCES_JSON, "r", encoding="utf-8") as f:
        coco_data = json.load(f)

    cat_id_to_name = {c["id"]: c["name"] for c in coco_data["categories"]}
    name_to_cat_id = {c["name"]: c["id"] for c in coco_data["categories"]}

    target_cat_ids = {name_to_cat_id[name] for name in TARGET_CLASSES if name in name_to_cat_id}
    print(f"[*] Kelas target ({len(target_cat_ids)}): {', '.join(TARGET_CLASSES)}")

    # 1. Kelompokkan anotasi dan cari gambar crowd
    images_by_id = {img["id"]: img for img in coco_data["images"]}
    annos_by_image = defaultdict(list)
    crowd_images = set()

    for ann in coco_data["annotations"]:
        img_id = ann["image_id"]
        if ann.get("iscrowd", 0) == 1:
            crowd_images.add(img_id)
        annos_by_image[img_id].append(ann)

    # 2. Seleksi gambar untuk tiap kelas
    # Pastikan person hanya pada gambar tanpa iscrowd
    selected_images_per_class = defaultdict(list)
    for cat_name in TARGET_CLASSES:
        cat_id = name_to_cat_id[cat_name]
        for img_id, anns in annos_by_image.items():
            if img_id in crowd_images:
                continue  # Lewati gambar dengan kerumunan tak terpisah
            matching_anns = [a for a in anns if a["category_id"] == cat_id]
            if matching_anns:
                selected_images_per_class[cat_name].append(img_id)
                if len(selected_images_per_class[cat_name]) >= MIN_IMAGES_PER_CLASS:
                    break

    all_selected_image_ids = set()
    for cat_name, img_ids in selected_images_per_class.items():
        print(f"    - {cat_name:<12}: {len(img_ids)} gambar terpilih")
        all_selected_image_ids.update(img_ids)

    print(f"[*] Total gambar unik yang akan diunduh: {len(all_selected_image_ids)}")

    # 3. Unduh gambar COCO secara asinkron
    print("[*] Mengunduh gambar dari COCO dataset...")
    t0 = time.time()
    conn = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=conn) as session:
        tasks = []
        for img_id in all_selected_image_ids:
            p = OUTPUT_DIR / f"{img_id:012d}.jpg"
            tasks.append(download_image(session, img_id, p))
        await asyncio.gather(*tasks)

    dt = time.time() - t0
    print(f"[OK] Pengunduhan selesai dalam {dt:.1f} detik.")

    # 4. Bangun metadata subset
    subset_images = []
    subset_annotations = []
    class_instance_counts = defaultdict(int)

    for img_id in sorted(all_selected_image_ids):
        img_info = images_by_id[img_id]
        img_file = f"{img_id:012d}.jpg"
        subset_images.append({
            "id": img_id,
            "file_name": img_file,
            "width": img_info["width"],
            "height": img_info["height"],
        })
        for ann in annos_by_image[img_id]:
            cid = ann["category_id"]
            if cid in target_cat_ids:
                cname = cat_id_to_name[cid]
                class_instance_counts[cname] += 1
                subset_annotations.append({
                    "id": ann["id"],
                    "image_id": img_id,
                    "category_id": cid,
                    "class_name": cname,
                    # bbox COCO: [x, y, width, height]
                    "bbox": [round(float(v), 2) for v in ann["bbox"]],
                    "area": ann.get("area", 0.0),
                })

    subset_payload = {
        "info": {
            "description": "COCO val2017 evaluation subset untuk Smart Home 'Rumah' Vision AI",
            "source": "http://cocodataset.org",
            "license": "CC BY 4.0",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "target_classes": TARGET_CLASSES,
        },
        "images": subset_images,
        "annotations": subset_annotations,
    }

    with open(SUBSET_JSON, "w", encoding="utf-8") as f:
        json.dump(subset_payload, f, indent=2)

    print(f"\n[OK] Metadata tersimpan di {SUBSET_JSON}:")
    print(f"    - Total gambar : {len(subset_images)}")
    print(f"    - Total anotasi: {len(subset_annotations)}")
    print("    - Rincian Objek per Kelas:")
    for cname in TARGET_CLASSES:
        print(f"      * {cname:<12}: {class_instance_counts[cname]} objek")


if __name__ == "__main__":
    asyncio.run(main())
