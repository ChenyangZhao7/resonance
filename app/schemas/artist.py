from pydantic import BaseModel
from typing import Optional

class ArtistBase(BaseModel):
    name: str
    genre: Optional[str] = None
    popularity: Optional[int] = 0

class ArtistCreate(ArtistBase):
    pass

class ArtistUpdate(ArtistBase):
    name: Optional[str] = None

class ArtistResponse(ArtistBase):
    id: int

    class Config:
        from_attributes = True
