import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401  (registers the ORM models on Base.metadata)
from app.database import Base, enable_sqlite_foreign_keys, get_db
from app.main import app
from app.models.artist import Artist
from app.models.song import Song


@pytest.fixture()
def db_session(tmp_path):
    """A throwaway SQLite database per test: tests never touch music.db."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    enable_sqlite_foreign_keys(engine)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def seeded_db(db_session):
    pop = Artist(name="Pop Artist", genre="pop", popularity=80)
    rock = Artist(name="Rock Artist", genre="rock", popularity=70)
    db_session.add_all([pop, rock])
    db_session.commit()

    db_session.add_all(
        [
            Song(title="Pop One", artist_id=pop.id, genre="pop", popularity=90,
                 danceability=0.8, energy=0.8, valence=0.9, tempo=120,
                 acousticness=0.1, speechiness=0.05),
            Song(title="Pop Two", artist_id=pop.id, genre="pop", popularity=85,
                 danceability=0.7, energy=0.7, valence=0.8, tempo=118,
                 acousticness=0.15, speechiness=0.06),
            Song(title="Rock One", artist_id=rock.id, genre="rock", popularity=60,
                 danceability=0.4, energy=0.9, valence=0.3, tempo=140,
                 acousticness=0.2, speechiness=0.08),
            Song(title="Calm One", artist_id=rock.id, genre="ambient", popularity=55,
                 danceability=0.3, energy=0.3, valence=0.2, tempo=90,
                 acousticness=0.8, speechiness=0.03),
            Song(title="Jazz One", artist_id=rock.id, genre="jazz", popularity=40,
                 danceability=0.5, energy=0.2, valence=0.6, tempo=100,
                 acousticness=0.9, speechiness=0.04),
            Song(title="Pop Three", artist_id=pop.id, genre="pop", popularity=30,
                 danceability=0.85, energy=0.85, valence=0.95, tempo=125,
                 acousticness=0.05, speechiness=0.07),
        ]
    )
    db_session.commit()
    return db_session


def _override_db(session):
    def _get_db():
        yield session

    return _get_db


@pytest.fixture()
def client(seeded_db):
    app.dependency_overrides[get_db] = _override_db(seeded_db)
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def empty_client(db_session):
    app.dependency_overrides[get_db] = _override_db(db_session)
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    credentials = {
        "username": "pytest_user",
        "email": "pytest@example.com",
        "password": "testpass123",
    }
    client.post("/auth/register", json=credentials)
    response = client.post(
        "/auth/login",
        data={
            "username": credentials["username"],
            "password": credentials["password"],
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
