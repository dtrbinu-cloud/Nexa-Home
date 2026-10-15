import datetime
import time
from typing import Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.core.config import settings
from server.app.models.assistant import AssistantDailyUsage


class AssistantRateLimiter:
    def __init__(self):
        # user_id -> list of timestamps
        self._user_requests: Dict[int, List[float]] = {}

    def check_user_rate_limit(self, user_id: int) -> bool:
        """Mengecek apakah user melebihi ASSISTANT_RATE_LIMIT_PER_MINUTE."""
        now = time.time()
        window = 60.0
        timestamps = self._user_requests.setdefault(user_id, [])
        # Hapus timestamp di luar window 1 menit
        timestamps[:] = [t for t in timestamps if now - t < window]

        if len(timestamps) >= settings.ASSISTANT_RATE_LIMIT_PER_MINUTE:
            return False

        timestamps.append(now)
        return True

    async def check_and_increment_daily_budget(
        self, db: AsyncSession, estimated_tokens: int = 50
    ) -> bool:
        """
        Mengecek kuota harian sistem (maksimum request & estimasi biaya).
        Mengembalikan True jika masih di dalam batas anggaran, False jika terlampaui.
        """
        today_str = datetime.date.today().isoformat()
        stmt = select(AssistantDailyUsage).where(AssistantDailyUsage.date_str == today_str)
        result = await db.execute(stmt)
        usage = result.scalars().first()

        if usage is None:
            usage = AssistantDailyUsage(
                date_str=today_str,
                total_requests=1,
                total_tokens=estimated_tokens,
                estimated_cost_cents=(estimated_tokens / 1000.0) * 0.1,  # estimasi ~$0.001 per 1k token
            )
            db.add(usage)
            await db.commit()
            return True

        # Cek batas request harian
        if usage.total_requests >= settings.ASSISTANT_DAILY_REQUEST_LIMIT:
            return False

        # Cek batas anggaran harian
        if usage.estimated_cost_cents >= settings.ASSISTANT_DAILY_BUDGET_CENTS:
            return False

        usage.total_requests += 1
        usage.total_tokens += estimated_tokens
        usage.estimated_cost_cents += (estimated_tokens / 1000.0) * 0.1
        await db.commit()
        return True


rate_limiter = AssistantRateLimiter()
