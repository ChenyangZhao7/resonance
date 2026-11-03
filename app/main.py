import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

import app.models  # noqa: F401  (registers the ORM models on Base.metadata)
from app.config import settings
from app.database import Base, engine
from app.routers import analytics, artists, auth, ratings, recommend, songs

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"


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
    docs_url=None,  # replaced below by a copy that uses local Swagger UI assets
    redoc_url=None,  # ReDoc is CDN-only, so /docs is the documented UI
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

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


@app.get("/docs", include_in_schema=False)
def swagger_docs():
    """Swagger UI served from local assets, so it works offline."""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        swagger_js_url="/static/swagger/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger/swagger-ui.css",
        swagger_favicon_url="/static/swagger/favicon-32x32.png",
    )


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
