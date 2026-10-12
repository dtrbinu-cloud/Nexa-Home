#!/usr/bin/env python3
"""
Pemeriksaan Kepatuhan Token Desain Otomatis — Smart Home "Rumah"
Memeriksa:
1. web/src/  : Tidak ada warna hex (#...) di luar file token.
2. app/lib/  : Tidak ada Color(0x...), Colors.xxx, atau hex (#...) di luar lib/theme/tokens.dart.
"""
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
WEB_SRC = ROOT_DIR / "web" / "src"
APP_LIB = ROOT_DIR / "app" / "lib"

WHITELISTED_WEB_FILES = {
    "design-tokens.css",
    "design-tokens.json",
}

WHITELISTED_DART_FILES = {
    "tokens.dart",
}

HEX_PATTERN = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
DART_COLOR_HEX = re.compile(r"Color\s*\(\s*0x[0-9a-fA-F]+\s*\)")
DART_MATERIAL_COLORS = re.compile(r"\bColors\.[a-zA-Z0-9_]+")


def check_web_tokens() -> list[tuple[str, int, str, str]]:
    violations = []
    if not WEB_SRC.exists():
        return violations

    for file_path in WEB_SRC.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix not in {".css", ".ts", ".tsx", ".js", ".jsx", ".html"}:
            continue
        if file_path.name in WHITELISTED_WEB_FILES:
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for line_num, line in enumerate(content.splitlines(), start=1):
            matches = HEX_PATTERN.findall(line)
            if matches:
                for match in matches:
                    rel_path = file_path.relative_to(ROOT_DIR)
                    violations.append((str(rel_path), line_num, match, line.strip()))
    return violations


def check_dart_tokens() -> list[tuple[str, int, str, str]]:
    violations = []
    if not APP_LIB.exists():
        return violations

    for file_path in APP_LIB.rglob("*.dart"):
        if not file_path.is_file():
            continue
        if file_path.name in WHITELISTED_DART_FILES:
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for line_num, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            # Abaikan komentar single-line
            if stripped.startswith("//"):
                continue

            # Cek Color(0x...)
            for match in DART_COLOR_HEX.findall(line):
                rel_path = file_path.relative_to(ROOT_DIR)
                violations.append((str(rel_path), line_num, match, stripped))

            # Cek Colors.xxx
            for match in DART_MATERIAL_COLORS.findall(line):
                rel_path = file_path.relative_to(ROOT_DIR)
                violations.append((str(rel_path), line_num, match, stripped))

            # Cek #HEX
            for match in HEX_PATTERN.findall(line):
                rel_path = file_path.relative_to(ROOT_DIR)
                violations.append((str(rel_path), line_num, match, stripped))

    return violations


def check_all() -> int:
    print("=== Memeriksa Kepatuhan Token Desain (Web & Flutter) ===")
    web_violations = check_web_tokens()
    dart_violations = check_dart_tokens()

    total_violations = web_violations + dart_violations

    if total_violations:
        print(f"\n[GAGAL] Ditemukan {len(total_violations)} pelanggaran token:")
        for path, line, val, raw in total_violations:
            print(f"  - {path}:{line} -> {val}")
            print(f"    '{raw}'")
        print("\nAturan Desain:")
        print("  - Web: gunakan 'var(--color-...)' dari design-tokens.css")
        print("  - Flutter: gunakan AppColors.*, AppSpacing.*, AppRadius.* dari lib/theme/tokens.dart")
        return 1

    print("[BERHASIL] Semua komponen (Web & Flutter) 100% mematuhi sistem token desain.")
    return 0


if __name__ == "__main__":
    sys.exit(check_all())
