import datetime
import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.models.automation import Automation, NotificationLog

logger = logging.getLogger("rumah.automation")


def evaluate_condition(current_val: Any, op: str, target_val: Any) -> bool:
    """Evaluate simple arithmetic or equality conditions."""
    try:
        if op == "==":
            return current_val == target_val
        elif op == "!=":
            return current_val != target_val
        elif op == ">":
            return float(current_val) > float(target_val)
        elif op == ">=":
            return float(current_val) >= float(target_val)
        elif op == "<":
            return float(current_val) < float(target_val)
        elif op == "<=":
            return float(current_val) <= float(target_val)
    except (ValueError, TypeError):
        return False
    return False


async def process_telemetry_automations(
    db: AsyncSession,
    device_id: str,
    sensors: Dict[str, Any],
    channels: Dict[str, Any],
    mqtt_publisher=None,
) -> List[Dict[str, Any]]:
    """Evaluate all active automations against received sensor and channel values."""
    query = select(Automation).where(Automation.is_enabled == True)
    result = await db.execute(query)
    automations = result.scalars().all()

    triggered_results = []

    for auto in automations:
        try:
            trigger_cfg = json.loads(auto.trigger_config)
            action_cfg = json.loads(auto.action_config)
        except Exception:
            continue

        target_dev = trigger_cfg.get("device_id")
        if target_dev and target_dev != device_id:
            continue

        sensor_key = trigger_cfg.get("sensor") or trigger_cfg.get("channel")
        op = trigger_cfg.get("op", "==")
        threshold = trigger_cfg.get("value")

        val = None
        if sensor_key in sensors:
            val = sensors[sensor_key]
        elif sensor_key in channels:
            val = channels[sensor_key]

        if val is None:
            continue

        if evaluate_condition(val, op, threshold):
            logger.info("Automation '%s' triggered by %s %s %s (val=%s)", auto.name, sensor_key, op, threshold, val)
            triggered_results.append({
                "automation_id": auto.id,
                "name": auto.name,
                "action": action_cfg,
            })

            # Eksekusi aksi: Notifikasi
            if action_cfg.get("notify") or action_cfg.get("type") == "notify":
                msg = action_cfg.get("message") or f"Otomasi '{auto.name}' terpicu."
                severity = action_cfg.get("severity", "info")
                notif = NotificationLog(
                    device_id=device_id,
                    event_type="automation_triggered",
                    message=msg,
                    severity=severity,
                )
                db.add(notif)

            # Eksekusi aksi: Perintah perangkat MQTT
            if (action_cfg.get("type") == "device_cmd" or "channel" in action_cfg) and mqtt_publisher:
                target_cmd_dev = action_cfg.get("device_id", device_id)
                ch = action_cfg.get("channel")
                act = action_cfg.get("action", "set")
                val_to_send = action_cfg.get("value")
                cmd_payload = {
                    "id": f"auto_{auto.id}_{int(datetime.datetime.utcnow().timestamp())}",
                    "channel": ch,
                    "action": act,
                    "value": val_to_send,
                }
                mqtt_publisher(target_cmd_dev, cmd_payload)

    if triggered_results:
        await db.commit()

    return triggered_results
