"""Content-based recommendation logic.

Everything here is deterministic: candidates are ordered by ``Song.id`` before
scoring, so repeated calls return the same ranking.
"""

import math
from collections import Counter

from sqlalchemy.orm import Session

from app.config import settings
from app.models.rating import Rating
from app.models.song import Song

FEATURES = (
    "danceability",
    "energy",
    "valence",
    "tempo",
    "acousticness",
    "speechiness",
)

# Spotify tempo is roughly 0-250 BPM; scale it so it does not dominate the
# cosine similarity with the 0-1 features.
TEMPO_SCALE = 200.0

MOOD_FILTERS = {
    "happy": {"valence_min": 0.6, "energy_min": 0.5},
    "sad": {"valence_max": 0.4, "energy_max": 0.5},
    "energetic": {"energy_min": 0.7, "danceability_min": 0.6},
    "calm": {"energy_max": 0.4, "acousticness_min": 0.5},
}

# Ratings at or above this value are treated as "the user likes this song".
POSITIVE_RATING = 3.0

WEIGHT_AUDIO = 0.75
WEIGHT_GENRE = 0.25


def _song_vector(song: Song) -> dict:
    vector = {feature: getattr(song, feature) or 0.0 for feature in FEATURES}
    vector["tempo"] = vector["tempo"] / TEMPO_SCALE
    return vector


def cosine_similarity(a: dict, b: dict) -> float:
    dot_product = sum(a.get(f, 0) * b.get(f, 0) for f in FEATURES)
    mag_a = math.sqrt(sum(a.get(f, 0) ** 2 for f in FEATURES))
    mag_b = math.sqrt(sum(b.get(f, 0) ** 2 for f in FEATURES))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot_product / (mag_a * mag_b)


def get_similar_songs(song_id: int, db: Session, limit: int = 10):
    """Return songs similar to ``song_id``, or ``None`` if the song is unknown."""
    target = db.get(Song, song_id)
    if target is None:
        return None

    target_vector = _song_vector(target)
    candidates = (
        db.query(Song)
        .filter(Song.id != song_id)
        .order_by(Song.id)
        .limit(settings.max_similar_candidates)
        .all()
    )

    scored = [(cosine_similarity(target_vector, _song_vector(song)), song) for song in candidates]
    scored.sort(key=lambda item: (-item[0], item[1].id))
    return [song for _, song in scored[:limit]]


def get_songs_by_mood(mood: str, db: Session, limit: int = 10):
    """Return songs matching a known mood.

    Raises ``ValueError`` for anything outside ``MOOD_FILTERS`` instead of
    silently returning arbitrary songs.
    """
    filters = MOOD_FILTERS.get(mood.lower())
    if filters is None:
        raise ValueError(
            f"Unknown mood '{mood}'. Supported moods: {', '.join(sorted(MOOD_FILTERS))}"
        )

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

    return (
        query.order_by(Song.popularity.desc(), Song.id)
        .limit(limit)
        .all()
    )


def _popular_fallback(db: Session, excluded_ids: set[int], limit: int):
    query = db.query(Song)
    if excluded_ids:
        query = query.filter(~Song.id.in_(excluded_ids))
    songs = query.order_by(Song.popularity.desc(), Song.id).limit(limit).all()
    return [
        (song, round((song.popularity or 0) / 100, 4), "popular track (no rating history yet)")
        for song in songs
    ]


def get_personal_recommendations(user_id: int, db: Session, limit: int = 10):
    """Recommend songs for a user based on the ratings they submitted.

    Builds a weighted taste profile from the songs the user rated and ranks
    unrated songs by audio-feature similarity plus a genre preference bonus.
    Users without ratings get popular songs instead.
    """
    ratings = db.query(Rating).filter(Rating.user_id == user_id).all()
    rated_ids = {rating.song_id for rating in ratings}
    positive = [rating for rating in ratings if rating.score >= POSITIVE_RATING]

    if not positive:
        return _popular_fallback(db, rated_ids, limit)

    rated_songs = {
        song.id: song for song in db.query(Song).filter(Song.id.in_(rated_ids)).all()
    }

    # Weight each rated song by how much the user liked it.
    weights = {}
    for rating in positive:
        if rating.song_id in rated_songs:
            weights[rating.song_id] = rating.score - (POSITIVE_RATING - 0.5)

    if not weights:
        return _popular_fallback(db, rated_ids, limit)

    profile = {feature: 0.0 for feature in FEATURES}
    total_weight = sum(weights.values())
    for song_id, weight in weights.items():
        vector = _song_vector(rated_songs[song_id])
        for feature in FEATURES:
            profile[feature] += vector[feature] * weight
    for feature in FEATURES:
        profile[feature] /= total_weight

    genre_scores = Counter()
    for song_id, weight in weights.items():
        genre = rated_songs[song_id].genre
        if genre:
            genre_scores[genre] += weight
    top_genres = {genre for genre, _ in genre_scores.most_common(3)}
    max_genre_score = max(genre_scores.values(), default=0) or 1

    candidates = (
        db.query(Song)
        .filter(~Song.id.in_(rated_ids))
        .order_by(Song.id)
        .limit(settings.max_similar_candidates)
        .all()
    )

    scored = []
    for song in candidates:
        audio_score = cosine_similarity(profile, _song_vector(song))
        genre_score = (
            genre_scores.get(song.genre, 0) / max_genre_score if song.genre else 0.0
        )
        score = WEIGHT_AUDIO * audio_score + WEIGHT_GENRE * genre_score
        if song.genre and song.genre in top_genres:
            reason = f"matches your taste in {song.genre}"
        else:
            reason = "similar audio profile to your highly rated songs"
        scored.append((song, round(min(max(score, 0.0), 1.0), 4), reason))

    scored.sort(key=lambda item: (-item[1], item[0].id))
    return scored[:limit]
