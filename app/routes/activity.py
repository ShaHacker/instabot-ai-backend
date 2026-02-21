from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.services.auth import get_current_user

router = APIRouter(prefix="/activity", tags=["Activity Log"])


@router.get("")
async def list_activity(
    action_type: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(ActivityLog).where(ActivityLog.user_id == user.id)
    count_query = select(func.count(ActivityLog.id)).where(ActivityLog.user_id == user.id)

    if action_type:
        query = query.where(ActivityLog.action_type == action_type)
        count_query = count_query.where(ActivityLog.action_type == action_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(ActivityLog.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    logs = result.scalars().all()

    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return {
        "logs": [
            {
                "id": log.id,
                "action_type": log.action_type,
                "details": log.details,
                "ig_username": log.ig_username,
                "post_id": log.post_id,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "pages": pages,
    }
