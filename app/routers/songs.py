from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.artist import Artist
from app.models.song import Song
from app.routers.auth import get_current_user
from app.schemas.song import SongCreate, SongResponse, SongUpdate

router = APIRouter(prefix="/songs", tags=["Songs"])


@router.get("/", response_model=List[SongResponse])
def get_songs(
    skip: int = Query(0, ge=0),
    limit: int = Query(
        settings.page_size_default, ge=1, le=settings.page_size_max
    ),
    db: Session = Depends(get_db),
):
    return db.query(Song).order_by(Song.id).offset(skip).limit(limit).all()


@router.get("/{song_id}", response_model=SongResponse)
def get_song(song_id: int, db: Session = Depends(get_db)):
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song


@router.post("/", response_model=SongResponse, status_code=201)
def create_song(
    song: SongCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if song.artist_id is not None and not db.get(Artist, song.artist_id):
        raise HTTPException(status_code=400, detail="Artist not found")

    db_song = Song(**song.model_dump())
    db.add(db_song)
    db.commit()
    db.refresh(db_song)
    return db_song


@router.put("/{song_id}", response_model=SongResponse)
def update_song(
    song_id: int,
    song: SongUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_song = db.get(Song, song_id)
    if not db_song:
        raise HTTPException(status_code=404, detail="Song not found")

    updates = song.model_dump(exclude_unset=True)
    if "artist_id" in updates and updates["artist_id"] is not None:
        if not db.get(Artist, updates["artist_id"]):
            raise HTTPException(status_code=400, detail="Artist not found")

    for key, value in updates.items():
        setattr(db_song, key, value)
    db.commit()
    db.refresh(db_song)
    return db_song


@router.delete("/{song_id}", status_code=204)
def delete_song(
    song_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_song = db.get(Song, song_id)
    if not db_song:
        raise HTTPException(status_code=404, detail="Song not found")
    db.delete(db_song)
    db.commit()
