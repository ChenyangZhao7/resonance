import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models.artist import Artist
from app.models.song import Song
import app.models

Base.metadata.create_all(bind=engine)

def import_data():
    db = SessionLocal()
    print("Reading dataset...")
    df = pd.read_csv("data/dataset.csv")
    df = df.dropna(subset=["track_name", "artists"])
    df = df.head(5000)

    print(f"Importing {len(df)} songs...")
    artist_cache = {}

    for _, row in df.iterrows():
        artist_name = str(row["artists"]).split(";")[0].strip()

        if artist_name not in artist_cache:
            artist = db.query(Artist).filter(Artist.name == artist_name).first()
            if not artist:
                artist = Artist(
                    name=artist_name,
                    genre=str(row.get("track_genre", "")),
                    popularity=int(row.get("popularity", 0))
                )
                db.add(artist)
                db.commit()
                db.refresh(artist)
            artist_cache[artist_name] = artist.id

        existing = db.query(Song).filter(Song.spotify_id == str(row.get("track_id", ""))).first()
        if not existing:
            song = Song(
                title=str(row["track_name"]),
                artist_id=artist_cache[artist_name],
                genre=str(row.get("track_genre", "")),
                duration_ms=int(row.get("duration_ms", 0)),
                popularity=int(row.get("popularity", 0)),
                danceability=float(row.get("danceability", 0)),
                energy=float(row.get("energy", 0)),
                valence=float(row.get("valence", 0)),
                tempo=float(row.get("tempo", 0)),
                acousticness=float(row.get("acousticness", 0)),
                speechiness=float(row.get("speechiness", 0)),
                spotify_id=str(row.get("track_id", ""))
            )
            db.add(song)

    db.commit()
    db.close()
    print("Import complete!")

if __name__ == "__main__":
    import_data()
