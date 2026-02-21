from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.ig_account import IGAccount
from app.schemas.settings import SettingsUpdate, SettingsResponse
from app.services.auth import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IGAccount).where(IGAccount.user_id == user.id))
    ig = result.scalar_one_or_none()

    # Mask the API key for display
    masked_key = None
    if user.gemini_api_key:
        masked_key = user.gemini_api_key[:8] + "..." + user.gemini_api_key[-4:]

    return SettingsResponse(
        gemini_api_key=masked_key,
        ai_tone=user.ai_tone or "friendly",
        custom_tone=user.custom_tone,
        default_language=user.default_language or "English",
        email_notifications=user.email_notifications or False,
        daily_summary=user.daily_summary or False,
        ig_connected=ig is not None,
        ig_username=ig.ig_username if ig else None,
        ig_profile_pic=ig.ig_profile_pic if ig else None,
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(data: SettingsUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if data.gemini_api_key is not None:
        user.gemini_api_key = data.gemini_api_key
    if data.ai_tone is not None:
        user.ai_tone = data.ai_tone
    if data.custom_tone is not None:
        user.custom_tone = data.custom_tone
    if data.default_language is not None:
        user.default_language = data.default_language
    if data.email_notifications is not None:
        user.email_notifications = data.email_notifications
    if data.daily_summary is not None:
        user.daily_summary = data.daily_summary

    result = await db.execute(select(IGAccount).where(IGAccount.user_id == user.id))
    ig = result.scalar_one_or_none()

    masked_key = None
    if user.gemini_api_key:
        masked_key = user.gemini_api_key[:8] + "..." + user.gemini_api_key[-4:]

    return SettingsResponse(
        gemini_api_key=masked_key,
        ai_tone=user.ai_tone or "friendly",
        custom_tone=user.custom_tone,
        default_language=user.default_language or "English",
        email_notifications=user.email_notifications or False,
        daily_summary=user.daily_summary or False,
        ig_connected=ig is not None,
        ig_username=ig.ig_username if ig else None,
        ig_profile_pic=ig.ig_profile_pic if ig else None,
    )


@router.delete("/instagram")
async def disconnect_instagram(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IGAccount).where(IGAccount.user_id == user.id))
    ig = result.scalar_one_or_none()
    if not ig:
        raise HTTPException(status_code=400, detail="No Instagram account connected")

    await db.delete(ig)
    return {"detail": "Instagram account disconnected"}
