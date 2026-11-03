from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.song import Song
from app.schemas.song import SongCreate, SongUpdate, SongResponse

router = APIRouter(prefix="/songs", tags=["Songs"])

@router.get("/", response_model=List[SongResponse])
def get_songs(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(Song).offset(skip).limit(limit).all()

@router.get("/{song_id}", response_model=SongResponse)
def get_song(song_id: int, db: Session = Depends(get_db)):
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song

@router.post("/", response_model=SongResponse, status_code=201)
def create_song(song: SongCreate, db: Session = Depends(get_db)):
    db_song = Song(**song.dict())
    db.add(db_song)
    db.commit()
    db.refresh(db_song)
    return db_song

@router.put("/{song_id}", response_model=SongResponse)
def update_song(song_id: int, song: SongUpdate, db: Session = Depends(get_db)):
    db_song = db.query(Song).filter(Song.id == song_id).first()
    if not db_song:
        raise HTTPException(status_code=404, detail="Song not found")
    for key, value in song.dict(exclude_unset=True).items():
        setattr(db_song, key, value)
    db.commit()
    db.refresh(db_song)
    return db_song

@router.delete("/{song_id}", status_code=204)
def delete_song(song_id: int, db: Session = Depends(get_db)):
    db_song = db.query(Song).filter(Song.id == song_id).first()
    if not db_song:
        raise HTTPException(status_code=404, detail="Song not found")
    db.delete(db_song)
    db.commit()
