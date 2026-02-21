import httpx
from app.config import get_settings

settings = get_settings()

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


async def get_instagram_oauth_url() -> str:
    """Generate the Instagram OAuth URL for user login."""
    scopes = "instagram_basic,instagram_manage_comments,instagram_manage_messages,pages_show_list,pages_manage_metadata"
    return (
        f"https://www.facebook.com/v21.0/dialog/oauth"
        f"?client_id={settings.META_APP_ID}"
        f"&redirect_uri={settings.INSTAGRAM_REDIRECT_URI}"
        f"&scope={scopes}"
        f"&response_type=code"
    )


async def exchange_code_for_token(code: str) -> dict:
    """Exchange the OAuth code for a short-lived access token, then get long-lived token."""
    async with httpx.AsyncClient() as client:
        # Get short-lived token
        resp = await client.get(
            f"{GRAPH_API_BASE}/oauth/access_token",
            params={
                "client_id": settings.META_APP_ID,
                "client_secret": settings.META_APP_SECRET,
                "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
                "code": code,
            }
        )
        data = resp.json()
        short_token = data.get("access_token")
        if not short_token:
            raise ValueError(f"Failed to get access token: {data}")

        # Exchange for long-lived token
        resp = await client.get(
            f"{GRAPH_API_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.META_APP_ID,
                "client_secret": settings.META_APP_SECRET,
                "fb_exchange_token": short_token,
            }
        )
        long_data = resp.json()
        long_token = long_data.get("access_token", short_token)

        return {"access_token": long_token}


async def get_user_pages(access_token: str) -> list[dict]:
    """Get Facebook pages connected to the user's account."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GRAPH_API_BASE}/me/accounts",
            params={"access_token": access_token}
        )
        data = resp.json()
        return data.get("data", [])


async def get_instagram_account(page_id: str, page_access_token: str) -> dict | None:
    """Get the Instagram Business account connected to a Facebook page."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GRAPH_API_BASE}/{page_id}",
            params={
                "fields": "instagram_business_account",
                "access_token": page_access_token,
            }
        )
        data = resp.json()
        ig_account = data.get("instagram_business_account")
        if not ig_account:
            return None

        ig_id = ig_account["id"]
        # Get IG profile info
        resp = await client.get(
            f"{GRAPH_API_BASE}/{ig_id}",
            params={
                "fields": "username,profile_picture_url",
                "access_token": page_access_token,
            }
        )
        ig_data = resp.json()
        return {
            "ig_user_id": ig_id,
            "ig_username": ig_data.get("username"),
            "ig_profile_pic": ig_data.get("profile_picture_url"),
            "page_id": page_id,
            "page_access_token": page_access_token,
        }


async def get_user_media(ig_user_id: str, access_token: str) -> list[dict]:
    """Fetch recent media/posts from the Instagram account."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GRAPH_API_BASE}/{ig_user_id}/media",
            params={
                "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp",
                "limit": 25,
                "access_token": access_token,
            }
        )
        data = resp.json()
        return data.get("data", [])


async def reply_to_comment(comment_id: str, message: str, access_token: str) -> dict:
    """Reply to an Instagram comment."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GRAPH_API_BASE}/{comment_id}/replies",
            params={"access_token": access_token},
            data={"message": message}
        )
        return resp.json()


async def send_dm(ig_user_id: str, recipient_id: str, message: str, access_token: str) -> dict:
    """Send a DM to an Instagram user via the Messaging API."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GRAPH_API_BASE}/{ig_user_id}/messages",
            params={"access_token": access_token},
            json={
                "recipient": {"id": recipient_id},
                "message": {"text": message}
            }
        )
        return resp.json()
