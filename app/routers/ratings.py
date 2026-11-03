from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.rating import Rating
from app.models.song import Song
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.rating import RatingCreate, RatingResponse

router = APIRouter(prefix="/ratings", tags=["Ratings"])


@router.post("/", response_model=RatingResponse, status_code=201)
def rate_song(
    payload: RatingCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rate a song. Re-rating the same song updates the existing rating (200)."""
    if not db.get(Song, payload.song_id):
        raise HTTPException(status_code=404, detail="Song not found")

    rating = (
        db.query(Rating)
        .filter(
            Rating.user_id == current_user.id,
            Rating.song_id == payload.song_id,
        )
        .first()
    )

    if rating:
        rating.score = payload.score
        response.status_code = status.HTTP_200_OK
    else:
        rating = Rating(
            user_id=current_user.id,
            song_id=payload.song_id,
            score=payload.score,
        )
        db.add(rating)

    db.commit()
    db.refresh(rating)
    return rating


@router.get("/me", response_model=List[RatingResponse])
def list_my_ratings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Rating)
        .filter(Rating.user_id == current_user.id)
        .order_by(Rating.created_at.desc(), Rating.id.desc())
        .all()
    )


@router.delete("/{song_id}", status_code=204)
def delete_rating(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rating = (
        db.query(Rating)
        .filter(Rating.user_id == current_user.id, Rating.song_id == song_id)
        .first()
    )
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    db.delete(rating)
    db.commit()
