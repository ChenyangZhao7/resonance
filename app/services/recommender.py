from sqlalchemy.orm import Session
from app.models.song import Song
import math

def cosine_similarity(a: dict, b: dict) -> float:
    features = ["danceability", "energy", "valence", "tempo", "acousticness", "speechiness"]
    dot_product = sum(a.get(f, 0) * b.get(f, 0) for f in features)
    mag_a = math.sqrt(sum(a.get(f, 0) ** 2 for f in features))
    mag_b = math.sqrt(sum(b.get(f, 0) ** 2 for f in features))
    if mag_a == 0 or mag_b == 0:
        return 0
    return dot_product / (mag_a * mag_b)

def get_similar_songs(song_id: int, db: Session, limit: int = 10):
    target = db.query(Song).filter(Song.id == song_id).first()
    if not target:
        return []

    target_features = {
        "danceability": target.danceability or 0,
        "energy": target.energy or 0,
        "valence": target.valence or 0,
        "tempo": (target.tempo or 0) / 200,
        "acousticness": target.acousticness or 0,
        "speechiness": target.speechiness or 0,
    }

    songs = db.query(Song).filter(Song.id != song_id).limit(500).all()
    scored = []
    for song in songs:
        features = {
            "danceability": song.danceability or 0,
            "energy": song.energy or 0,
            "valence": song.valence or 0,
            "tempo": (song.tempo or 0) / 200,
            "acousticness": song.acousticness or 0,
            "speechiness": song.speechiness or 0,
        }
        score = cosine_similarity(target_features, features)
        scored.append((score, song))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [song for _, song in scored[:limit]]

def get_songs_by_mood(mood: str, db: Session, limit: int = 10):
    mood_filters = {
        "happy":    {"valence_min": 0.6, "energy_min": 0.5},
        "sad":      {"valence_max": 0.4, "energy_max": 0.5},
        "energetic":{"energy_min": 0.7, "danceability_min": 0.6},
        "calm":     {"energy_max": 0.4, "acousticness_min": 0.5},
    }

    filters = mood_filters.get(mood.lower(), {})
    query = db.query(Song)

    if "valence_min" in filters:
        query = query.filter(Song.valence >= filters["valence_min"])
    if "valence_max" in filters:
        query = query.filter(Song.valence <= filters["valence_max"])
    if "energy_min" in filters:
        query = query.filter(Song.energy >= filters["energy_min"])
    if "energy_max" in filters:
        query = query.filter(Song.energy <= filters["energy_max"])
    if "danceability_min" in filters:
        query = query.filter(Song.danceability >= filters["danceability_min"])
    if "acousticness_min" in filters:
        query = query.filter(Song.acousticness >= filters["acousticness_min"])

    return query.order_by(Song.popularity.desc()).limit(limit).all()
