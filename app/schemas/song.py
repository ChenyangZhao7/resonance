from typing import Optional

from pydantic import BaseModel, ConfigDict


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


class SongUpdate(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    mood: Optional[str] = None
    duration_ms: Optional[int] = None
    popularity: Optional[int] = None
    danceability: Optional[float] = None
    energy: Optional[float] = None
    valence: Optional[float] = None
    tempo: Optional[float] = None
    acousticness: Optional[float] = None
    speechiness: Optional[float] = None
    spotify_id: Optional[str] = None
    artist_id: Optional[int] = None


class SongResponse(SongBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
