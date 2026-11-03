from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.song import Song
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.recommend import Recommendation
from app.schemas.song import SongResponse
from app.services.recommender import (
    MOOD_FILTERS,
    get_personal_recommendations,
    get_similar_songs,
    get_songs_by_mood,
)

router = APIRouter(prefix="/recommend", tags=["Recommendations"])


def limit_param(
    limit: int = Query(
        settings.recommend_limit_default,
        ge=1,
        le=settings.recommend_limit_max,
        description="Number of songs to return",
    )
) -> int:
    return limit


@router.get("/similar/{song_id}", response_model=List[SongResponse])
def similar_songs(
    song_id: int, limit: int = Depends(limit_param), db: Session = Depends(get_db)
):
    songs = get_similar_songs(song_id, db, limit)
    if songs is None:
        raise HTTPException(status_code=404, detail="Song not found")
    return songs


@router.get("/mood", response_model=List[SongResponse])
def recommend_by_mood(
    mood: str = Query(
        ..., description=f"One of: {', '.join(sorted(MOOD_FILTERS))}"
    ),
    limit: int = Depends(limit_param),
    db: Session = Depends(get_db),
):
    try:
        songs = get_songs_by_mood(mood, db, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not songs:
        raise HTTPException(status_code=404, detail="No songs found for this mood")
    return songs


@router.get("/genre", response_model=List[SongResponse])
def recommend_by_genre(
    genre: str = Query(..., description="e.g. pop, rock, jazz"),
    limit: int = Depends(limit_param),
    db: Session = Depends(get_db),
):
    songs = (
        db.query(Song)
        .filter(Song.genre.ilike(f"%{genre}%"))
        .order_by(Song.popularity.desc(), Song.id)
        .limit(limit)
        .all()
    )
    if not songs:
        raise HTTPException(status_code=404, detail="No songs found for this genre")
    return songs


@router.get("/for-me", response_model=List[Recommendation])
def recommend_for_me(
    limit: int = Depends(limit_param),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Personalised recommendations built from the caller's ratings."""
    return [
        {"song": song, "score": score, "reason": reason}
        for song, score, reason in get_personal_recommendations(
            current_user.id, db, limit
        )
    ]
