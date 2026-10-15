"""
Konfigurasi Logging & Rotasi Log Otomatis — Tahap 7.
Membatasi ukuran berkas log maksimal 10 MB per berkas dengan retensi 5 file rotasi
(RotatingFileHandler) untuk mencegah kepenuhan disk pada server lokal Windows 10.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "logs"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB per berkas
LOG_BACKUP_COUNT = 5  # Simpan hingga 5 berkas rotasi (.1, .2, dst)


def setup_rotating_logging(app_name: str = "rumah") -> None:
    """Inisialisasi handler rotasi berkas untuk seluruh logger sistem."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 1. Main Application Log (server.log)
    server_log_file = LOG_DIR / "server.log"
    server_handler = RotatingFileHandler(
        str(server_log_file),
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    server_handler.setLevel(logging.INFO)
    server_handler.setFormatter(log_format)

    # 2. Error Only Log (error.log)
    error_log_file = LOG_DIR / "error.log"
    error_handler = RotatingFileHandler(
        str(error_log_file),
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(log_format)

    # Tambahkan handler jika belum ada untuk mencegah duplikasi
    existing_handler_files = [
        getattr(h, "baseFilename", None) for h in root_logger.handlers if isinstance(h, RotatingFileHandler)
    ]

    if str(server_log_file) not in existing_handler_files:
        root_logger.addHandler(server_handler)
    if str(error_log_file) not in existing_handler_files:
        root_logger.addHandler(error_handler)

    logging.getLogger("uvicorn.access").addHandler(server_handler)
    logging.getLogger("uvicorn.error").addHandler(server_handler)
    logging.getLogger("server").setLevel(logging.INFO)
