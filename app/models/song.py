from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    artist_id = Column(Integer, ForeignKey("artists.id"))
    genre = Column(String, index=True)
    mood = Column(String)
    duration_ms = Column(Integer)
    popularity = Column(Integer, default=0)

    # Spotify audio features
    danceability = Column(Float)
    energy = Column(Float)
    valence = Column(Float)      # 0=sad, 1=happy
    tempo = Column(Float)
    acousticness = Column(Float)
    speechiness = Column(Float)
    spotify_id = Column(String, unique=True)

    artist = relationship("Artist", back_populates="songs")
    ratings = relationship("Rating", back_populates="song")