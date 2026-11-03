"""Import the Spotify Tracks Dataset into the database.

Usage:
    python data/import_spotify.py [path/to/dataset.csv] [max_rows]

The CSV is not stored in the repository (20 MB). Download it from Kaggle:
https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset
"""

import os
import sys

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.models  # noqa: F401,E402  (registers the ORM models)
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models.artist import Artist  # noqa: E402
from app.models.song import Song  # noqa: E402

DEFAULT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset.csv")
BATCH_SIZE = 500


def import_data(csv_path: str = DEFAULT_CSV, max_rows: int = 5000) -> None:
    if not os.path.exists(csv_path):
        raise SystemExit(
            f"Dataset not found: {csv_path}\n"
            "Download it from Kaggle and place it at data/dataset.csv."
        )

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print(f"Reading {csv_path}...")
        df = pd.read_csv(csv_path)
        df = df.dropna(subset=["track_name", "artists"]).head(max_rows)
        print(f"Importing {len(df)} songs...")

        artist_cache = {
            name: artist_id
            for artist_id, name in db.query(Artist.id, Artist.name).all()
        }
        existing_track_ids = {
            track_id for (track_id,) in db.query(Song.spotify_id).all() if track_id
        }

        added = 0
        for index, row in enumerate(df.itertuples(index=False), start=1):
            artist_name = str(row.artists).split(";")[0].strip()
            track_id = str(getattr(row, "track_id", "")) or None

            if track_id and track_id in existing_track_ids:
                continue

            artist_id = artist_cache.get(artist_name)
            if artist_id is None:
                artist = Artist(
                    name=artist_name,
                    genre=str(getattr(row, "track_genre", "")),
                    popularity=int(getattr(row, "popularity", 0) or 0),
                )
                db.add(artist)
                db.flush()  # assign artist.id without a full commit
                artist_id = artist.id
                artist_cache[artist_name] = artist_id

            db.add(
                Song(
                    title=str(row.track_name),
                    artist_id=artist_id,
                    genre=str(getattr(row, "track_genre", "")),
                    duration_ms=int(getattr(row, "duration_ms", 0) or 0),
                    popularity=int(getattr(row, "popularity", 0) or 0),
                    danceability=float(getattr(row, "danceability", 0) or 0),
                    energy=float(getattr(row, "energy", 0) or 0),
                    valence=float(getattr(row, "valence", 0) or 0),
                    tempo=float(getattr(row, "tempo", 0) or 0),
                    acousticness=float(getattr(row, "acousticness", 0) or 0),
                    speechiness=float(getattr(row, "speechiness", 0) or 0),
                    spotify_id=track_id,
                )
            )
            if track_id:
                existing_track_ids.add(track_id)

            if index % BATCH_SIZE == 0:
                db.commit()
                print(f"  {index}/{len(df)} rows processed")

        db.commit()
        print("Import complete!")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    csv_argument = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    rows = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    import_data(csv_argument, rows)
