import json
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.api.deps import require_role
from server.app.core.database import get_db
from server.app.models.audit import AuditLog
from server.app.models.user import User

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("")
async def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve system audit logs. Strictly restricted to admin role."""
    query = (
        select(AuditLog)
        .order_by(desc(AuditLog.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "status": "ok",
        "count": len(logs),
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "username": log.username,
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "details": json.loads(log.details) if log.details else None,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }
