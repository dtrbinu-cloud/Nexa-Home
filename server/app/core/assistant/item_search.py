"""
Layanan Pencarian Barang (find_item) berbasis Vision AI (Tahap 5).
- Memetakan kata pengguna dan sinonim bahasa Indonesia ke kelas COCO.
- Menolak barang di luar kelas COCO (kunci, dompet) dengan jujur.
- Menegakkan RBAC per peran (child ditolak, member hanya kamera diizinkan).
- Menyertakan lokasi, waktu terakhir terlihat, deskripsi posisi, dan thumbnail terenkripsi.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.models.camera import Camera, CameraUserAccess, DetectedItemLog
from server.app.models.user import User

logger = logging.getLogger("server.assistant.item_search")

# Pemetaan sinonim Bahasa Indonesia ke kelas COCO
COCO_SYNONYMS: Dict[str, str] = {
    # Handphone / Gadget
    "hp": "cell phone",
    "handphone": "cell phone",
    "ponsel": "cell phone",
    "telepon": "cell phone",
    "smartphone": "cell phone",
    "cell phone": "cell phone",
    "phone": "cell phone",

    # Remote
    "remote": "remote",
    "remot": "remote",
    "pengendali": "remote",
    "remote tv": "remote",
    "remote ac": "remote",

    # Komputer & Elektronik
    "laptop": "laptop",
    "notebook": "laptop",
    "komputer": "laptop",
    "mouse": "mouse",
    "tetikus": "mouse",
    "keyboard": "keyboard",
    "papan ketik": "keyboard",

    # Tas & Koper
    "tas": "handbag",
    "tas jinjing": "handbag",
    "tas tangan": "handbag",
    "handbag": "handbag",
    "ransel": "backpack",
    "tas ransel": "backpack",
    "tas punggung": "backpack",
    "backpack": "backpack",
    "koper": "suitcase",
    "suitcase": "suitcase",

    # Wadah Minuman
    "botol": "bottle",
    "botol minum": "bottle",
    "bottle": "bottle",
    "cangkir": "cup",
    "gelas": "cup",
    "mug": "cup",
    "cup": "cup",

    # Buku
    "buku": "book",
    "kitab": "book",
    "novel": "book",
    "majalah": "book",
    "book": "book",

    # Lainnya
    "payung": "umbrella",
    "umbrella": "umbrella",
}

# Barang kecil umum di luar kelas COCO yang belum didukung
UNSUPPORTED_ITEMS: Dict[str, str] = {
    "kunci": "kunci",
    "kunci rumah": "kunci rumah",
    "kunci motor": "kunci motor",
    "kunci mobil": "kunci mobil",
    "dompet": "dompet",
    "wallet": "dompet",
    "kartu": "kartu identitas/ATM",
    "kacamata": "kacamata",
    "cincin": "cincin",
    "jam tangan": "jam tangan",
    "uang": "uang",
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def format_position_description(x: float, y: float) -> str:
    """Mengubah koordinat bounding box normalisasi menjadi deskripsi letak manusiawi."""
    horizontal = "di tengah"
    if x < 0.33:
        horizontal = "di sisi kiri"
    elif x > 0.66:
        horizontal = "di sisi kanan"

    vertical = "ruangan"
    if y < 0.35:
        vertical = "area belakang/atas"
    elif y > 0.65:
        vertical = "area depan/bawah"

    return f"{horizontal} ({vertical})"


async def execute_find_item(
    db: AsyncSession,
    user: User,
    query: str,
) -> Dict[str, Any]:
    """
    Mencari lokasi barang berdasarkan log Vision AI dengan verifikasi RBAC.
    """
    clean_query = query.strip().lower()

    # 1. Verifikasi Izin Peran: Child Ditolak Keras
    if user.role == "child":
        return {
            "status": "forbidden",
            "error": "Akses ditolak: Akun anak (child) tidak memiliki izin untuk mencari data barang kamera pengawas.",
        }

    # 2. Cek Benda yang Belum Didukung (Jujur dan Terus Terang)
    for unsupp_key, label in UNSUPPORTED_ITEMS.items():
        if unsupp_key in clean_query:
            return {
                "status": "unsupported",
                "message": (
                    f"Pencarian {label} belum didukung oleh sistem. "
                    f"Model Vision AI saat ini hanya mengenali benda-benda dalam kelas dataset COCO "
                    f"(seperti HP, remote, tas, laptop, botol, cangkir, buku, dan payung). "
                    f"Benda kecil seperti {label} belum dapat dideteksi secara akurat."
                ),
            }

    # 3. Pencocokan Sinonim ke Kelas COCO
    target_coco_classes: List[str] = []
    matched_term = clean_query

    # Cek kecocokan langsung atau substring
    for term, coco_cls in COCO_SYNONYMS.items():
        if term == clean_query or term in clean_query:
            if term == "tas":
                target_coco_classes = ["handbag", "backpack"]
            else:
                target_coco_classes = [coco_cls]
            matched_term = term
            break

    if not target_coco_classes:
        return {
            "status": "unknown_class",
            "message": (
                f"Benda '{query}' belum dikenali dalam daftar pencarian Vision AI. "
                f"Barang yang dapat dicari meliputi: HP, remote, laptop, tas/ransel, koper, botol, cangkir, buku, payung."
            ),
        }

    # 4. Filter Kamera Sesuai Hak Akses (Member)
    allowed_camera_ids: Optional[set] = None
    if user.role == "member":
        access_stmt = select(CameraUserAccess.camera_id).where(CameraUserAccess.user_id == user.id)
        rules = (await db.execute(access_stmt)).scalars().all()
        if rules:
            allowed_camera_ids = set(rules)

    # 5. Cari di Database Log Benda (DetectedItemLog)
    stmt = (
        select(DetectedItemLog)
        .where(DetectedItemLog.class_name.in_(target_coco_classes))
        .order_by(DetectedItemLog.last_seen_at.desc())
    )
    if allowed_camera_ids is not None:
        stmt = stmt.where(DetectedItemLog.camera_id.in_(allowed_camera_ids))

    item = (await db.execute(stmt)).scalars().first()

    if not item:
        return {
            "status": "not_found",
            "message": f"{matched_term.upper()} belum pernah terdeteksi di kamera ruangan yang aktif.",
            "class_name": target_coco_classes[0],
        }

    # 6. Format Jawaban Waktu dan Posisi
    last_dt = item.last_seen_at
    if last_dt.tzinfo is None:
        last_dt = last_dt.replace(tzinfo=timezone.utc)

    now = utcnow()
    diff_sec = (now - last_dt).total_seconds()

    # Format jam lokal (HH.MM)
    time_str = last_dt.strftime("%H.%M")
    pos_desc = format_position_description(item.bbox_x, item.bbox_y)

    age_warning = ""
    if diff_sec > 86400:
        days = int(diff_sec // 86400)
        age_warning = f" (Perhatian: data ini sudah {days} hari yang lalu)"
    elif diff_sec > 3600 * 6:
        hours = int(diff_sec // 3600)
        age_warning = f" (Perhatian: data ini sudah {hours} jam yang lalu)"

    reply_msg = (
        f"{matched_term.upper()} terakhir terlihat di {item.room_id}, "
        f"sekitar pukul {time_str}, {pos_desc}.{age_warning}"
    )

    thumb_url = f"/api/cameras/{item.camera_id}/items/{item.id}/thumbnail" if item.thumbnail_path else None

    return {
        "status": "success",
        "message": reply_msg,
        "item_id": item.id,
        "camera_id": item.camera_id,
        "room_id": item.room_id,
        "class_name": item.class_name,
        "confidence": item.confidence,
        "last_seen_at": item.last_seen_at.isoformat(),
        "thumbnail_url": thumb_url,
    }
