import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.database import init_db
from app.routes import auth, posts, qa, flows, leads, dashboard, activity, settings, webhook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting InstaBot AI Backend...")
    await init_db()
    logger.info("Database tables created.")
    yield
    logger.info("Shutting down InstaBot AI Backend...")


app = FastAPI(
    title="InstaBot AI",
    description="Instagram AI Automation Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[app_settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers under /api/v1
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(posts.router, prefix=API_PREFIX)
app.include_router(qa.router, prefix=API_PREFIX)
app.include_router(flows.router, prefix=API_PREFIX)
app.include_router(leads.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(activity.router, prefix=API_PREFIX)
app.include_router(settings.router, prefix=API_PREFIX)
app.include_router(webhook.router, prefix=API_PREFIX)


@app.get("/")
async def root():
    return {"message": "InstaBot AI Backend is running", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=app_settings.HOST,
        port=app_settings.PORT,
        reload=True,
    )
