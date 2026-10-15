#!/usr/bin/env python3
"""
scripts/sysinfo.py — Informasi Sistem dan Perangkat Keras Pengujian
Mencetak model CPU, jumlah core fisik & thread logika, flag instruksi AVX/VNNI nyata, dan RAM.
"""

import ctypes
import os
import platform
import sys
import winreg
from pathlib import Path
import psutil


def get_cpu_brand_windows() -> str:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
        )
        name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
        return name.strip()
    except Exception:
        return platform.processor() or "Unknown CPU"


def get_cpu_flags_x86_64():
    """Membaca flag instruksi CPUID nyata di arsitektur x86_64."""
    flags = {
        "AVX": False,
        "AVX2": False,
        "AVX512F": False,
        "AVX512_VNNI": False,
        "AVX_VNNI": False,
    }

    if platform.machine().lower() not in ("amd64", "x86_64"):
        return flags

    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.VirtualAlloc.restype = ctypes.c_void_p
        kernel32.VirtualAlloc.argtypes = [
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_ulong,
            ctypes.c_ulong,
        ]

        # Machine code x64: void cpuid(int leaf, int subleaf, int* regs)
        # rcx = leaf, rdx = subleaf, r8 = regs pointer
        code = bytes([
            0x89, 0xC8,             # mov eax, ecx
            0x89, 0xD1,             # mov ecx, edx
            0x53,                   # push rbx
            0x0F, 0xA2,             # cpuid
            0x41, 0x89, 0x00,       # mov [r8], eax
            0x41, 0x89, 0x58, 0x04, # mov [r8+4], ebx
            0x41, 0x89, 0x48, 0x08, # mov [r8+8], ecx
            0x41, 0x89, 0x50, 0x0C, # mov [r8+12], edx
            0x5B,                   # pop rbx
            0xC3,                   # ret
        ])

        addr = kernel32.VirtualAlloc(0, len(code), 0x3000, 0x40)
        if not addr:
            return flags

        ctypes.memmove(addr, code, len(code))
        func = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)(addr)

        regs = (ctypes.c_uint32 * 4)()
        p_regs = ctypes.cast(regs, ctypes.c_void_p).value

        # Leaf 1: ECX bit 28 = AVX
        func(1, 0, p_regs)
        flags["AVX"] = bool(regs[2] & (1 << 28))

        # Leaf 7, Subleaf 0: EBX bit 5 = AVX2, bit 16 = AVX512F, ECX bit 11 = AVX512_VNNI
        func(7, 0, p_regs)
        flags["AVX2"] = bool(regs[1] & (1 << 5))
        flags["AVX512F"] = bool(regs[1] & (1 << 16))
        flags["AVX512_VNNI"] = bool(regs[2] & (1 << 11))

        # Leaf 7, Subleaf 1: EAX bit 4 = AVX_VNNI
        func(7, 1, p_regs)
        flags["AVX_VNNI"] = bool(regs[0] & (1 << 4))

        kernel32.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong]
        kernel32.VirtualFree(addr, 0, 0x8000)
    except Exception as e:
        pass

    return flags


def main():
    cpu_name = get_cpu_brand_windows()
    cores = psutil.cpu_count(logical=False) or 0
    threads = psutil.cpu_count(logical=True) or 0
    mem = psutil.virtual_memory()
    total_ram_gb = mem.total / (1024 ** 3)
    available_ram_gb = mem.available / (1024 ** 3)
    flags = get_cpu_flags_x86_64()

    print("=" * 60)
    print("INFORMASI SISTEM & SPESIFIKASI PERANGKAT KERAS PENGUJIAN")
    print("=" * 60)
    print(f"Model CPU          : {cpu_name}")
    print(f"Jumlah Core Fisik  : {cores} cores")
    print(f"Jumlah Thread      : {threads} threads")
    print(f"Total RAM          : {total_ram_gb:.2f} GB (Tersedia: {available_ram_gb:.2f} GB)")
    print(f"Sistem Operasi     : {platform.system()} {platform.release()} ({platform.architecture()[0]})")
    print("-" * 60)
    print("Flag Instruksi Akselerasi AI (Hardware CPUID):")
    print(f"  - AVX            : {'DIDUKUNG' if flags['AVX'] else 'TIDAK DIDUKUNG'}")
    print(f"  - AVX2           : {'DIDUKUNG' if flags['AVX2'] else 'TIDAK DIDUKUNG'}")
    print(f"  - AVX-512F       : {'DIDUKUNG' if flags['AVX512F'] else 'TIDAK DIDUKUNG'}")
    print(f"  - AVX-512 VNNI   : {'DIDUKUNG' if flags['AVX512_VNNI'] else 'TIDAK DIDUKUNG'}")
    print(f"  - AVX VNNI       : {'DIDUKUNG' if flags['AVX_VNNI'] else 'TIDAK DIDUKUNG'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
