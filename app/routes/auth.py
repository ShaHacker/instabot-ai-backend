from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.ig_account import IGAccount
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse
from app.services.auth import hash_password, verify_password, create_access_token, get_current_user
from app.services.instagram import get_instagram_oauth_url, exchange_code_for_token, get_user_pages, get_instagram_account
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/register", response_model=Token)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    await db.flush()

    token = create_access_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IGAccount).where(IGAccount.user_id == user.id))
    ig = result.scalar_one_or_none()
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        is_active=user.is_active,
        ig_connected=ig is not None,
        ig_username=ig.ig_username if ig else None,
    )


@router.get("/instagram")
async def instagram_oauth(user: User = Depends(get_current_user)):
    url = await get_instagram_oauth_url()
    return {"oauth_url": url}


@router.get("/instagram/callback")
async def instagram_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Handle the OAuth callback from Meta. Exchanges code for token and saves IG account."""
    try:
        token_data = await exchange_code_for_token(code)
        access_token = token_data["access_token"]

        pages = await get_user_pages(access_token)
        if not pages:
            return RedirectResponse(f"{settings.FRONTEND_URL}/settings?error=no_pages")

        # Use the first page that has an Instagram account
        ig_data = None
        for page in pages:
            ig_data = await get_instagram_account(page["id"], page["access_token"])
            if ig_data:
                break

        if not ig_data:
            return RedirectResponse(f"{settings.FRONTEND_URL}/settings?error=no_ig_account")

        # For now, redirect to frontend with success
        # The frontend should call a separate endpoint to link the account
        # In production, you'd use a state parameter to identify the user
        return RedirectResponse(
            f"{settings.FRONTEND_URL}/settings?ig_connected=true&ig_username={ig_data['ig_username']}"
        )

    except Exception as e:
        return RedirectResponse(f"{settings.FRONTEND_URL}/settings?error={str(e)}")
