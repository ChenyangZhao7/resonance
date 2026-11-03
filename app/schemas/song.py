from pydantic import BaseModel
from typing import Optional

class SongBase(BaseModel):
    title: str
    genre: Optional[str] = None
    mood: Optional[str] = None
    duration_ms: Optional[int] = None
    popularity: Optional[int] = 0
    danceability: Optional[float] = None
    energy: Optional[float] = None
    valence: Optional[float] = None
    tempo: Optional[float] = None
    acousticness: Optional[float] = None
    speechiness: Optional[float] = None
    spotify_id: Optional[str] = None
    artist_id: Optional[int] = None

class SongCreate(SongBase):
    pass

class SongUpdate(SongBase):
    title: Optional[str] = None

class SongResponse(SongBase):
    id: int

    class Config:
        from_attributes = True
