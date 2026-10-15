"""
Modul Enkripsi dan Dekripsi Klip Video Rekaman Gerakan (AES-256-GCM).
Kunci simetris diambil secara eksklusif dari .env dan TIDAK PERNAH disimpan di database.
"""

import hashlib
import os
from pathlib import Path
from typing import Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from server.app.core.config import settings


def get_encryption_key() -> bytes:
    """Mengambil kunci enkripsi 32-byte (256-bit) dari settings/config (.env).
    Mendukung kunci terpadu MEDIA_ENCRYPTION_KEY dengan fallback mundur ke
    RECORDING_ENCRYPTION_KEY dan CAMERA_ENCRYPTION_KEY tanpa merusak data lama.
    """
    raw_key = (
        settings.MEDIA_ENCRYPTION_KEY
        or settings.RECORDING_ENCRYPTION_KEY
        or settings.CAMERA_ENCRYPTION_KEY
        or "rumah_default_secret_key_recording_32b"
    )
    # Jika panjang 64 hex karakter, konversi dari hex
    if len(raw_key) == 64:
        try:
            return bytes.fromhex(raw_key)
        except ValueError:
            pass
    # Standarisasi menjadi tepat 32 bytes via SHA-256
    return hashlib.sha256(raw_key.encode("utf-8")).digest()


def encrypt_bytes(data: bytes, associated_data: str = "") -> Tuple[bytes, str]:
    """
    Enkripsi data biner menggunakan AES-256-GCM.
    Returns: (ciphertext_termasuk_tag, nonce_hex)
    """
    key = get_encryption_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce standar AES-GCM
    aad = associated_data.encode("utf-8") if associated_data else None
    ciphertext = aesgcm.encrypt(nonce, data, aad)
    return ciphertext, nonce.hex()


def decrypt_bytes(ciphertext: bytes, nonce_hex: str, associated_data: str = "") -> bytes:
    """
    Dekripsi data biner terenkripsi menggunakan AES-256-GCM.
    Throws InvalidTag jika kunci salah atau data telah diubah/rusak.
    """
    key = get_encryption_key()
    aesgcm = AESGCM(key)
    nonce = bytes.fromhex(nonce_hex)
    aad = associated_data.encode("utf-8") if associated_data else None
    return aesgcm.decrypt(nonce, ciphertext, aad)


def save_encrypted_clip(data: bytes, camera_id: str, output_path: Path) -> Tuple[str, int]:
    """Enkripsi rekaman video dan simpan ke berkas disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ciphertext, nonce_hex = encrypt_bytes(data, associated_data=camera_id)
    output_path.write_bytes(ciphertext)
    return nonce_hex, len(ciphertext)


def read_and_decrypt_clip(file_path: Path, nonce_hex: str, camera_id: str) -> bytes:
    """Membaca berkas terenkripsi dari disk dan mendekripsinya secara on-the-fly."""
    if not file_path.exists():
        raise FileNotFoundError(f"Berkas rekaman tidak ditemukan di path: {file_path}")
    ciphertext = file_path.read_bytes()
    return decrypt_bytes(ciphertext, nonce_hex, associated_data=camera_id)


def encrypt_clip_data(data: bytes, camera_id: str) -> Tuple[bytes, str]:
    """Helper untuk mengenkripsi data byte dengan associated data camera_id."""
    return encrypt_bytes(data, associated_data=camera_id)


def decrypt_clip_data(ciphertext: bytes, camera_id: str, nonce_hex: str) -> bytes:
    """Helper untuk mendekripsi data byte dengan associated data camera_id."""
    return decrypt_bytes(ciphertext, nonce_hex, associated_data=camera_id)
