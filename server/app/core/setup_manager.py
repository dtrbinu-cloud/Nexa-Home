import ipaddress
import secrets
from typing import Optional

_SETUP_CODE: Optional[str] = None


PROXY_HEADERS = {
    "x-forwarded-for",
    "x-forwarded-host",
    "x-forwarded-proto",
    "x-real-ip",
    "forwarded",
    "via",
    "cf-connecting-ip",
    "true-client-ip",
    "x-cluster-client-ip",
}


def has_proxy_headers(headers: dict) -> bool:
    """Check if any reverse proxy or tunnel headers are present."""
    lowered = {k.lower(): v for k, v in headers.items()}
    for h in PROXY_HEADERS:
        if h in lowered and lowered[h].strip():
            return True
    return False


def is_lan_or_localhost(client_ip: Optional[str]) -> bool:
    """Check if client IP belongs to localhost or private LAN (RFC1918 / ULA)."""
    if not client_ip:
        return False
    # Bersihkan jika ada port atau format testclient
    ip_str = client_ip.split(":")[0].strip()
    if ip_str in {"localhost", "testclient", "test"}:
        return True

    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return ip_obj.is_loopback or ip_obj.is_private or ip_obj.is_link_local
    except ValueError:
        return False


def get_current_setup_code() -> Optional[str]:
    """Return the active setup code, if any."""
    global _SETUP_CODE
    return _SETUP_CODE


def init_setup_code_if_needed(has_admin: bool) -> Optional[str]:
    """Generate and display setup code in console if no admin exists."""
    global _SETUP_CODE
    if has_admin:
        _SETUP_CODE = None
        return None

    if _SETUP_CODE is None:
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        random_suffix = "".join(secrets.choice(chars) for _ in range(6))
        _SETUP_CODE = f"RUMAH-{random_suffix}"

        print("\n" + "=" * 64)
        print(" [SETUP WIZARD] Belum ada akun admin terdaftar!")
        print(f" KODE SETUP SEKALI PAKAI: {_SETUP_CODE}")
        print(" Masukkan kode ini di aplikasi untuk inisialisasi akun admin.")
        print(" Hanya dapat diakses dari Localhost atau Jaringan Lokal (LAN).")
        print("=" * 64 + "\n", flush=True)

    return _SETUP_CODE


def verify_and_consume_setup_code(input_code: str) -> bool:
    """Validate setup code and immediately invalidate it upon success."""
    global _SETUP_CODE
    if not _SETUP_CODE:
        return False
    if input_code.strip().upper() == _SETUP_CODE.upper():
        _SETUP_CODE = None  # Konsumsi sekali pakai
        return True
    return False


def reset_setup_code_for_testing():
    """Helper for testing environment."""
    global _SETUP_CODE
    _SETUP_CODE = None
