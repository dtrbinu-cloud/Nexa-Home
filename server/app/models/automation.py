import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from server.app.core.database import Base


class Automation(Base):
    __tablename__ = "automations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    trigger_type = Column(String(50), nullable=False)  # "sensor_threshold", "state_change"
    trigger_config = Column(Text, nullable=False)  # JSON: {"device_id": "...", "channel": "...", "op": ">=", "value": 1500}
    action_config = Column(Text, nullable=False)  # JSON: {"device_id": "...", "channel": "...", "action": "set", "value": true}
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class NotificationLog(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(50), nullable=True)
    event_type = Column(String(50), nullable=False)  # "gas_alarm", "device_offline", "automation_triggered"
    message = Column(String(255), nullable=False)
    severity = Column(String(20), default="info", nullable=False)  # "info", "warning", "critical"
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True, nullable=False)
