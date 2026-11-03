from pydantic import BaseModel

from app.schemas.song import SongResponse


class Recommendation(BaseModel):
    song: SongResponse
    score: float
    reason: str
