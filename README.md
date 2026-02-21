# InstaBot AI - Backend

Instagram AI Automation Backend built with FastAPI, PostgreSQL, and Google Gemini AI.

## Features

- **Comment Automation** — AI-powered keyword matching and auto-replies to Instagram comments
- **DM Automation** — Smart DM replies + lead collection flows
- **Q&A Bank** — Semantic matching of comments to saved Q&A pairs
- **Lead Management** — Collect, track, and export leads
- **Dashboard** — Stats, charts, and activity logs
- **Excel Export** — Download leads as .xlsx

## Tech Stack

- **FastAPI** — async Python web framework
- **PostgreSQL** — database (Supabase/Neon free tier)
- **SQLAlchemy** — async ORM
- **Google Gemini** — AI for smart matching and reply generation
- **Instagram Graph API** — official Meta API for comments and DMs

## Setup

### 1. Clone and install dependencies

```bash
cd instabot-ai-backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### 2. Set up environment variables

```bash
copy .env.example .env
```

Edit `.env` with your values:

| Variable | Where to get it |
|---|---|
| `DATABASE_URL` | Supabase → Project Settings → Database → Connection String (use `postgresql+asyncpg://`) |
| `DATABASE_URL_SYNC` | Same but with `postgresql://` prefix |
| `SECRET_KEY` | Any random string (use `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey |
| `META_APP_ID` | https://developers.facebook.com → Your App → Settings |
| `META_APP_SECRET` | Same as above |
| `META_WEBHOOK_VERIFY_TOKEN` | Any string you choose (used to verify webhook) |
| `FRONTEND_URL` | Your Lovable frontend URL |

### 3. Set up free PostgreSQL database

**Option A: Supabase (recommended)**
1. Go to https://supabase.com → New Project
2. Copy the connection string from Settings → Database
3. Replace `[YOUR-PASSWORD]` and use `postgresql+asyncpg://` prefix

**Option B: Neon.tech**
1. Go to https://neon.tech → Create Project
2. Copy the connection string

### 4. Run the server

```bash
python main.py
```

Server starts at http://localhost:8000

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 5. Set up Meta Developer App (for Instagram API)

1. Go to https://developers.facebook.com
2. Create a new app → Select "Business" type
3. Add products: **Instagram Graph API** and **Webhooks**
4. In Instagram Graph API settings, add your redirect URI
5. Set up Webhooks:
   - Callback URL: `https://your-server.com/api/v1/webhook`
   - Verify Token: same as `META_WEBHOOK_VERIFY_TOKEN` in .env
   - Subscribe to: `comments`, `messages`

### 6. Connect frontend

Set the frontend's `VITE_API_URL` environment variable to your backend URL:
```
VITE_API_URL=http://localhost:8000/api/v1
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/auth/me` | Get current user |
| GET | `/api/v1/auth/instagram` | Get Instagram OAuth URL |
| GET | `/api/v1/auth/instagram/callback` | OAuth callback |
| GET | `/api/v1/dashboard/stats` | Dashboard statistics |
| GET | `/api/v1/dashboard/chart` | Chart data (7 days) |
| GET | `/api/v1/posts` | List posts |
| POST | `/api/v1/posts/sync` | Sync posts from Instagram |
| GET | `/api/v1/posts/{id}` | Get post with keywords |
| PUT | `/api/v1/posts/{id}/toggle` | Toggle automation |
| POST | `/api/v1/posts/{id}/keywords` | Add keyword rule |
| DELETE | `/api/v1/posts/{id}/keywords/{kid}` | Delete keyword |
| GET | `/api/v1/qa` | List Q&A pairs |
| POST | `/api/v1/qa` | Create Q&A |
| PUT | `/api/v1/qa/{id}` | Update Q&A |
| DELETE | `/api/v1/qa/{id}` | Delete Q&A |
| GET | `/api/v1/flows` | List DM flows |
| POST | `/api/v1/flows` | Create flow |
| PUT | `/api/v1/flows/{id}` | Update flow |
| DELETE | `/api/v1/flows/{id}` | Delete flow |
| GET | `/api/v1/leads` | List leads (paginated, filterable) |
| PUT | `/api/v1/leads/{id}/status` | Update lead status |
| GET | `/api/v1/leads/export/excel` | Export leads to Excel |
| GET | `/api/v1/activity` | Activity log (paginated) |
| GET | `/api/v1/settings` | Get settings |
| PUT | `/api/v1/settings` | Update settings |
| DELETE | `/api/v1/settings/instagram` | Disconnect Instagram |
| GET | `/api/v1/webhook` | Webhook verification |
| POST | `/api/v1/webhook` | Webhook event handler |

## Free Tier Limits

| Service | Limit |
|---|---|
| Supabase | 500MB database, 50K rows |
| Gemini API | 15 req/min, 1M tokens/day |
| Instagram API | No limit (official API) |
| Render.com | Sleeps after 15 min inactivity |
