from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.song import Song
from app.models.artist import Artist

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/genre-trends")
def genre_trends(db: Session = Depends(get_db)):
    results = db.query(
        Song.genre,
        func.count(Song.id).label("count"),
        func.avg(Song.popularity).label("avg_popularity")
    ).group_by(Song.genre).order_by(func.count(Song.id).desc()).limit(10).all()

    return [
        {
            "genre": r.genre,
            "count": r.count,
            "avg_popularity": round(r.avg_popularity or 0, 2)
        }
        for r in results
    ]

@router.get("/mood-distribution")
def mood_distribution(db: Session = Depends(get_db)):
    total = db.query(Song).count()
    happy = db.query(Song).filter(Song.valence >= 0.6, Song.energy >= 0.5).count()
    sad = db.query(Song).filter(Song.valence <= 0.4, Song.energy <= 0.5).count()
    energetic = db.query(Song).filter(Song.energy >= 0.7, Song.danceability >= 0.6).count()
    calm = db.query(Song).filter(Song.energy <= 0.4, Song.acousticness >= 0.5).count()

    return {
        "total_songs": total,
        "mood_breakdown": {
            "happy": {"count": happy, "percentage": round(happy / total * 100, 1)},
            "sad": {"count": sad, "percentage": round(sad / total * 100, 1)},
            "energetic": {"count": energetic, "percentage": round(energetic / total * 100, 1)},
            "calm": {"count": calm, "percentage": round(calm / total * 100, 1)},
        }
    }

@router.get("/top-artists")
def top_artists(limit: int = 10, db: Session = Depends(get_db)):
    results = db.query(
        Artist.name,
        func.count(Song.id).label("song_count"),
        func.avg(Song.popularity).label("avg_popularity")
    ).join(Song).group_by(Artist.id).order_by(func.avg(Song.popularity).desc()).limit(limit).all()

    return [
        {
            "artist": r.name,
            "song_count": r.song_count,
            "avg_popularity": round(r.avg_popularity or 0, 2)
        }
        for r in results
    ]

@router.get("/audio-features-summary")
def audio_features_summary(db: Session = Depends(get_db)):
    result = db.query(
        func.avg(Song.danceability).label("avg_danceability"),
        func.avg(Song.energy).label("avg_energy"),
        func.avg(Song.valence).label("avg_valence"),
        func.avg(Song.tempo).label("avg_tempo"),
        func.avg(Song.acousticness).label("avg_acousticness"),
    ).first()

    return {
        "avg_danceability": round(result.avg_danceability or 0, 3),
        "avg_energy": round(result.avg_energy or 0, 3),
        "avg_valence": round(result.avg_valence or 0, 3),
        "avg_tempo": round(result.avg_tempo or 0, 2),
        "avg_acousticness": round(result.avg_acousticness or 0, 3),
    }
