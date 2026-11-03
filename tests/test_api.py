from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Music Recommendation API"

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_songs():
    response = client.get("/songs/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_artists():
    response = client.get("/artists/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_and_delete_artist():
    response = client.post("/artists/", json={
        "name": "Test Artist",
        "genre": "pop",
        "popularity": 50
    })
    assert response.status_code == 201
    artist_id = response.json()["id"]

    response = client.delete(f"/artists/{artist_id}")
    assert response.status_code == 204

def test_create_and_delete_song():
    artist = client.post("/artists/", json={"name": "Test Artist 2", "genre": "rock"})
    artist_id = artist.json()["id"]

    response = client.post("/songs/", json={
        "title": "Test Song",
        "genre": "rock",
        "artist_id": artist_id,
        "popularity": 50
    })
    assert response.status_code == 201
    song_id = response.json()["id"]

    response = client.delete(f"/songs/{song_id}")
    assert response.status_code == 204

    client.delete(f"/artists/{artist_id}")

def test_song_not_found():
    response = client.get("/songs/99999")
    assert response.status_code == 404

def test_artist_not_found():
    response = client.get("/artists/99999")
    assert response.status_code == 404

def test_recommend_by_mood():
    response = client.get("/recommend/mood?mood=happy")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_recommend_by_genre():
    response = client.get("/recommend/genre?genre=acoustic")
    assert response.status_code == 200

def test_recommend_similar():
    response = client.get("/recommend/similar/1")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_genre_trends():
    response = client.get("/analytics/genre-trends")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_mood_distribution():
    response = client.get("/analytics/mood-distribution")
    assert response.status_code == 200
    data = response.json()
    assert "total_songs" in data
    assert "mood_breakdown" in data

def test_top_artists():
    response = client.get("/analytics/top-artists")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_register_user():
    response = client.post("/auth/register", json={
        "username": "pytest_user",
        "email": "pytest@example.com",
        "password": "testpass123"
    })
    assert response.status_code in [201, 400]

def test_login_user():
    client.post("/auth/register", json={
        "username": "login_test_user",
        "email": "logintest@example.com",
        "password": "testpass123"
    })
    response = client.post("/auth/login", data={
        "username": "login_test_user",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
