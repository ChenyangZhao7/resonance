from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RatingCreate(BaseModel):
    song_id: int
    score: float = Field(ge=1, le=5, description="Rating from 1.0 to 5.0")


class RatingUpdate(BaseModel):
    score: float = Field(ge=1, le=5)


class RatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    song_id: int
    score: float
    created_at: Optional[datetime] = None
