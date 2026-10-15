import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from server.app.core.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user", "assistant", "system", "tool"
    content = Column(Text, nullable=False)
    tool_calls = Column(Text, nullable=True)  # JSON string
    tool_call_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="chat_messages")


class PendingConfirmation(Base):
    __tablename__ = "pending_confirmations"

    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_id = Column(Integer, nullable=True)
    device_id = Column(String(50), nullable=True)
    channel_key = Column(String(50), nullable=True)
    channel_name = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)  # "turn_on", "turn_off", "all_on", "all_off"
    description = Column(Text, nullable=False)
    is_confirmed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class AssistantDailyUsage(Base):
    __tablename__ = "assistant_daily_usage"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date_str = Column(String(10), unique=True, index=True, nullable=False)  # YYYY-MM-DD
    total_requests = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost_cents = Column(Float, default=0.0, nullable=False)
