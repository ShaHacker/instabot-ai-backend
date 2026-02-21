from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.user import User
from app.models.lead import Lead
from app.models.post import Post
from app.models.activity_log import ActivityLog
from app.models.conversation import Conversation
from app.services.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_stats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Total leads
    leads_result = await db.execute(select(func.count(Lead.id)).where(Lead.user_id == user.id))
    total_leads = leads_result.scalar() or 0

    # Replies sent today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    replies_result = await db.execute(
        select(func.count(ActivityLog.id)).where(
            ActivityLog.user_id == user.id,
            ActivityLog.action_type.in_(["comment_reply", "dm_sent"]),
            ActivityLog.created_at >= today_start,
        )
    )
    replies_today = replies_result.scalar() or 0

    # Active automations
    automations_result = await db.execute(
        select(func.count(Post.id)).where(Post.user_id == user.id, Post.automation_enabled == True)
    )
    active_automations = automations_result.scalar() or 0

    # DM conversations
    conversations_result = await db.execute(
        select(func.count(Conversation.id)).join(Lead).where(Lead.user_id == user.id)
    )
    dm_conversations = conversations_result.scalar() or 0

    return {
        "total_leads": total_leads,
        "replies_today": replies_today,
        "active_automations": active_automations,
        "dm_conversations": dm_conversations,
    }


@router.get("/chart")
async def get_chart_data(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get replies per day for the last 7 days."""
    data = []
    now = datetime.now(timezone.utc)

    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        result = await db.execute(
            select(func.count(ActivityLog.id)).where(
                ActivityLog.user_id == user.id,
                ActivityLog.action_type.in_(["comment_reply", "dm_sent"]),
                ActivityLog.created_at >= day_start,
                ActivityLog.created_at < day_end,
            )
        )
        count = result.scalar() or 0
        data.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "day": day_start.strftime("%a"),
            "replies": count,
        })

    return data
