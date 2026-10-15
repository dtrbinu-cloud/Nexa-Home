import sqlite3

def purge():
    conn = sqlite3.connect('server/data/rumah.db')
    c = conn.cursor()

    # 1. Hapus dummy devices
    c.execute("DELETE FROM devices WHERE id != 'esp32_559ed8'")
    print("Deleted dummy devices, rows affected:", c.rowcount)

    # 2. Hapus dummy channels
    c.execute("DELETE FROM channels WHERE device_id != 'esp32_559ed8' OR channel_key IN ('lamp', 'relay_fan')")
    print("Deleted dummy channels, rows affected:", c.rowcount)

    # 3. Hapus dummy cameras
    c.execute("DELETE FROM cameras")
    print("Deleted dummy cameras, rows affected:", c.rowcount)

    # 4. Hapus telemetry lama dari dummy devices
    c.execute("DELETE FROM telemetry_logs WHERE device_id != 'esp32_559ed8'")
    print("Deleted dummy telemetry, rows affected:", c.rowcount)

    conn.commit()

    print("\nRemaining devices:")
    for row in c.execute("SELECT id, name, is_online, last_seen_at FROM devices").fetchall():
        print(" ", row)

    print("\nRemaining channels:")
    for row in c.execute("SELECT device_id, channel_key, name, channel_type, current_value FROM channels").fetchall():
        print(" ", row)

    print("\nRemaining cameras:")
    for row in c.execute("SELECT * FROM cameras").fetchall():
        print(" ", row)

    conn.close()

if __name__ == '__main__':
    purge()
