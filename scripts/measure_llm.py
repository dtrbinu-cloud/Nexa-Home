"""
Skrip Pengukur TTFT (Time-To-First-Token) DeepSeek LLM.
Hanya berjalan jika DEEPSEEK_API_KEY valid terkonfigurasi di .env.
Mencegah pelaporan angka fiktif jika tidak ada API key aktif.
"""

import os
import sys
import time
from pathlib import Path

# Cari path repo root dan .env
REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / ".env"


def load_env_vars() -> dict[str, str]:
    vars_dict = {}
    if not ENV_FILE.exists():
        return vars_dict
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            vars_dict[k.strip()] = v.strip().strip('"').strip("'")
    return vars_dict


def main():
    env_vars = load_env_vars()
    api_key = env_vars.get("DEEPSEEK_API_KEY", "").strip()
    base_url = env_vars.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model_name = env_vars.get("DEEPSEEK_MODEL", "deepseek-chat")

    # Validasi API key: cek apakah kosong atau sekadar placeholder template
    placeholders = {
        "",
        "your_deepseek_api_key_here",
        "your_api_key_here",
        "ganti_dengan_api_key",
        "sk-dummy",
    }
    if not api_key or api_key in placeholders or api_key.startswith("your_"):
        print("=" * 60)
        print("PENGUKURAN TTFT DEEPSEEK LLM DIBATALKAN")
        print("=" * 60)
        print("[!] DEEPSEEK_API_KEY tidak ditemukan atau masih bernilai placeholder di .env.")
        print("    Pengukuran TTFT nyata DIBATALKAN untuk mencegah pelaporan angka fiktif.")
        print("    Angka TTFT sebelumnya (4,55 detik) pada Tahap 3 merupakan simulasi internal/mock,")
        print("    bukan pengukuran koneksi langsung ke server DeepSeek.")
        print()
        print("Untuk mengukur TTFT nyata:")
        print("1. Buka berkas .env")
        print("2. Masukkan DEEPSEEK_API_KEY=sk-xxxx resmi dari platform.deepseek.com")
        print("3. Jalankan kembali: python scripts/measure_llm.py")
        print("=" * 60)
        sys.exit(0)

    try:
        import httpx
    except ImportError:
        print("[!] httpx belum terpasang. Jalankan pip install httpx terlebih dahulu.")
        sys.exit(1)

    print(f"[*] Menghubungi DeepSeek API di {base_url} (Model: {model_name})...")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "Jawab singkat satu kata: Siapa kamu?"}
        ],
        "stream": True,
        "max_tokens": 50,
    }

    start_time = time.perf_counter()
    first_token_time = None
    accumulated_content = []

    try:
        with httpx.Client(timeout=30.0) as client:
            with client.stream("POST", f"{base_url}/chat/completions", headers=headers, json=payload) as response:
                if response.status_code != 200:
                    err_body = response.read().decode("utf-8", errors="ignore")
                    print(f"[!] Permintaan API gagal dengan status HTTP {response.status_code}: {err_body}")
                    sys.exit(1)

                for chunk in response.iter_lines():
                    if not chunk:
                        continue
                    if chunk.startswith("data: "):
                        data_str = chunk[6:].strip()
                        if data_str == "[DONE]":
                            break
                        import json
                        try:
                            parsed = json.loads(data_str)
                            delta = parsed.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                if first_token_time is None:
                                    first_token_time = time.perf_counter()
                                accumulated_content.append(content)
                        except Exception:
                            continue

        total_time = time.perf_counter() - start_time
        if first_token_time is not None:
            ttft = first_token_time - start_time
            print("=" * 60)
            print("HASIL PENGUKURAN TTFT DEEPSEEK SUNGGUHAN:")
            print(f"- Time-To-First-Token (TTFT) : {ttft:.3f} detik")
            print(f"- Total Durasi Respons        : {total_time:.3f} detik")
            print(f"- Respons Diterima            : {''.join(accumulated_content).strip()}")
            print("=" * 60)
        else:
            print("[!] Respons selesai tanpa token konten yang terbaca.")

    except Exception as exc:
        print(f"[!] Gagal menghubungi API DeepSeek: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
