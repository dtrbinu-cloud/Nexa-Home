@echo off
title Nexa Home - Sync ESP32 Firmware
cd /d "%~dp0\.."
echo Menyinkronkan firmware ke ESP32...
server\.venv\Scripts\python.exe scripts\sync_to_esp32.py
pause
