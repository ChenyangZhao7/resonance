from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.artist import Artist
from app.routers.auth import get_current_user
from app.schemas.artist import ArtistCreate, ArtistResponse, ArtistUpdate

router = APIRouter(prefix="/artists", tags=["Artists"])


@router.get("/", response_model=List[ArtistResponse])
def get_artists(
    skip: int = Query(0, ge=0),
    limit: int = Query(
        settings.page_size_default, ge=1, le=settings.page_size_max
    ),
    db: Session = Depends(get_db),
):
    return db.query(Artist).order_by(Artist.id).offset(skip).limit(limit).all()


@router.get("/{artist_id}", response_model=ArtistResponse)
def get_artist(artist_id: int, db: Session = Depends(get_db)):
    artist = db.get(Artist, artist_id)
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    return artist


@router.post("/", response_model=ArtistResponse, status_code=201)
def create_artist(
    artist: ArtistCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_artist = Artist(**artist.model_dump())
    db.add(db_artist)
    db.commit()
    db.refresh(db_artist)
    return db_artist


@router.put("/{artist_id}", response_model=ArtistResponse)
def update_artist(
    artist_id: int,
    artist: ArtistUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_artist = db.get(Artist, artist_id)
    if not db_artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    for key, value in artist.model_dump(exclude_unset=True).items():
        setattr(db_artist, key, value)
    db.commit()
    db.refresh(db_artist)
    return db_artist


@router.delete("/{artist_id}", status_code=204)
def delete_artist(
    artist_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_artist = db.get(Artist, artist_id)
    if not db_artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    db.delete(db_artist)
    db.commit()
