from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (
        # One rating per user per song: POST /ratings updates the existing row.
        UniqueConstraint("user_id", "song_id", name="uq_ratings_user_song"),
        CheckConstraint("score >= 1 AND score <= 5", name="ck_ratings_score_range"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    song_id = Column(
        Integer, ForeignKey("songs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score = Column(Float, nullable=False)   # 1.0 to 5.0
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="ratings")
    song = relationship("Song", back_populates="ratings")
