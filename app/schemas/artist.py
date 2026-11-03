from typing import Optional

from pydantic import BaseModel, ConfigDict


class ArtistBase(BaseModel):
    name: str
    genre: Optional[str] = None
    popularity: Optional[int] = 0


class ArtistCreate(ArtistBase):
    pass


class ArtistUpdate(BaseModel):
    name: Optional[str] = None
    genre: Optional[str] = None
    popularity: Optional[int] = None


class ArtistResponse(ArtistBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
