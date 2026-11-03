from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    song_id = Column(Integer, ForeignKey("songs.id"), nullable=False)
    score = Column(Float, nullable=False)   # 1.0 to 5.0
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="ratings")
    song = relationship("Song", back_populates="ratings")