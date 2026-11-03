import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401  (registers the ORM models on Base.metadata)
from app.config import settings
from app.database import Base, engine
from app.routers import analytics, artists, auth, ratings, recommend, songs

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Creating tables on startup (instead of at import time) keeps imports
    # side-effect free, so tests can point the app at their own database.
    Base.metadata.create_all(bind=engine)
    if settings.uses_default_secret:
        logger.warning(
            "MRA_SECRET_KEY is not set; using the insecure development key. "
            "Set it before deploying."
        )
    yield


app = FastAPI(
    title="Music Recommendation API",
    description="A data-driven API for music discovery and personalised recommendations.",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(songs.router)
app.include_router(artists.router)
app.include_router(ratings.router)
app.include_router(recommend.router)
app.include_router(analytics.router)


@app.get("/")
def root():
    return {
        "message": "Music Recommendation API",
        "docs": "/docs",
        "version": "1.1.0",
        "resources": [
            "/auth",
            "/songs",
            "/artists",
            "/ratings",
            "/recommend",
            "/analytics",
        ],
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
