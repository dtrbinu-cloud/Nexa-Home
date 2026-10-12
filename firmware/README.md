# Firmware ESP32 — Smart Home "Rumah"

Direktori ini berisi firmware MicroPython untuk modul hardware IoT ESP32.

## Struktur
- `legacy/esp32_thonny.py`: Cadangan kode firmware lama berbasis polling HTTP / MQTT lama.
- `src/` (Tahap 2): Kode firmware baru yang dirancang ulang dengan:
  - Transport MQTT sebagai kanal utama dengan LWT (`home/{device_id}/availability`)
  - Payload JSON terstruktur (`{channel, action, id}`)
  - Pemisahan kredensial ke `secrets.py` (tidak masuk git)
  - Non-blocking buzzer dan perlindungan mandiri alarm sensor MQ2 saat offline
