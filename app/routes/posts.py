from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.user import User
from app.models.post import Post
from app.models.keyword import Keyword
from app.models.ig_account import IGAccount
from app.schemas.posts import PostResponse, PostDetailResponse, KeywordCreate, KeywordResponse, PostToggle
from app.services.auth import get_current_user
from app.services.instagram import get_user_media
from datetime import datetime, timezone

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("", response_model=list[PostResponse])
async def list_posts(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Post).where(Post.user_id == user.id).order_by(Post.created_at.desc())
    )
    return result.scalars().all()


@router.post("/sync")
async def sync_posts(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Fetch latest posts from Instagram and sync to database."""
    result = await db.execute(select(IGAccount).where(IGAccount.user_id == user.id))
    ig_account = result.scalar_one_or_none()
    if not ig_account:
        raise HTTPException(status_code=400, detail="Instagram account not connected")

    media_list = await get_user_media(ig_account.ig_user_id, ig_account.page_access_token)
    synced = 0

    for media in media_list:
        existing = await db.execute(select(Post).where(Post.ig_post_id == media["id"]))
        if existing.scalar_one_or_none():
            continue

        post = Post(
            user_id=user.id,
            ig_post_id=media["id"],
            ig_media_url=media.get("media_url"),
            ig_thumbnail_url=media.get("thumbnail_url"),
            caption=media.get("caption"),
            media_type=media.get("media_type"),
            permalink=media.get("permalink"),
            ig_created_at=datetime.fromisoformat(media["timestamp"].replace("Z", "+00:00")) if media.get("timestamp") else None,
        )
        db.add(post)
        synced += 1

    return {"synced": synced, "total": len(media_list)}


@router.get("/{post_id}", response_model=PostDetailResponse)
async def get_post(post_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Post).options(selectinload(Post.keywords)).where(Post.id == post_id, Post.user_id == user.id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.put("/{post_id}/toggle", response_model=PostResponse)
async def toggle_automation(post_id: int, data: PostToggle, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.id == post_id, Post.user_id == user.id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.automation_enabled = data.automation_enabled
    return post


@router.post("/{post_id}/keywords", response_model=KeywordResponse)
async def add_keyword(post_id: int, data: KeywordCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.id == post_id, Post.user_id == user.id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    keyword = Keyword(
        post_id=post_id,
        keyword=data.keyword,
        reply_text=data.reply_text,
        reply_type=data.reply_type,
    )
    db.add(keyword)
    await db.flush()
    return keyword


@router.delete("/{post_id}/keywords/{keyword_id}")
async def delete_keyword(post_id: int, keyword_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Keyword).join(Post).where(Keyword.id == keyword_id, Post.id == post_id, Post.user_id == user.id)
    )
    keyword = result.scalar_one_or_none()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    await db.delete(keyword)
    return {"detail": "Keyword deleted"}
