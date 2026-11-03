from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.song import SongResponse
from app.services.recommender import get_similar_songs, get_songs_by_mood
from app.models.song import Song

router = APIRouter(prefix="/recommend", tags=["Recommendations"])

@router.get("/similar/{song_id}", response_model=List[SongResponse])
def similar_songs(song_id: int, limit: int = 10, db: Session = Depends(get_db)):
    songs = get_similar_songs(song_id, db, limit)
    if not songs:
        raise HTTPException(status_code=404, detail="Song not found")
    return songs

@router.get("/mood", response_model=List[SongResponse])
def recommend_by_mood(
    mood: str = Query(..., description="happy, sad, energetic, calm"),
    limit: int = 10,
    db: Session = Depends(get_db)
):
    songs = get_songs_by_mood(mood, db, limit)
    if not songs:
        raise HTTPException(status_code=404, detail="No songs found for this mood")
    return songs

@router.get("/genre", response_model=List[SongResponse])
def recommend_by_genre(
    genre: str = Query(..., description="e.g. pop, rock, jazz"),
    limit: int = 10,
    db: Session = Depends(get_db)
):
    songs = db.query(Song).filter(
        Song.genre.ilike(f"%{genre}%")
    ).order_by(Song.popularity.desc()).limit(limit).all()
    if not songs:
        raise HTTPException(status_code=404, detail="No songs found for this genre")
    return songs
