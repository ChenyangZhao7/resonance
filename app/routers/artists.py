from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.artist import Artist
from app.schemas.artist import ArtistCreate, ArtistUpdate, ArtistResponse

router = APIRouter(prefix="/artists", tags=["Artists"])

@router.get("/", response_model=List[ArtistResponse])
def get_artists(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(Artist).offset(skip).limit(limit).all()

@router.get("/{artist_id}", response_model=ArtistResponse)
def get_artist(artist_id: int, db: Session = Depends(get_db)):
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    return artist

@router.post("/", response_model=ArtistResponse, status_code=201)
def create_artist(artist: ArtistCreate, db: Session = Depends(get_db)):
    db_artist = Artist(**artist.dict())
    db.add(db_artist)
    db.commit()
    db.refresh(db_artist)
    return db_artist

@router.put("/{artist_id}", response_model=ArtistResponse)
def update_artist(artist_id: int, artist: ArtistUpdate, db: Session = Depends(get_db)):
    db_artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not db_artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    for key, value in artist.dict(exclude_unset=True).items():
        setattr(db_artist, key, value)
    db.commit()
    db.refresh(db_artist)
    return db_artist

@router.delete("/{artist_id}", status_code=204)
def delete_artist(artist_id: int, db: Session = Depends(get_db)):
    db_artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not db_artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    db.delete(db_artist)
    db.commit()
