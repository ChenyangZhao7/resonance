"""API tests.

Every test runs against a temporary SQLite database (see tests/conftest.py),
so the suite never reads or writes the real music.db.
"""


def _register_and_login(client, username="rating_user", email="rating@example.com"):
    client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": "testpass123"},
    )
    response = client.post(
        "/auth/login", data={"username": username, "password": "testpass123"}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


# --- basics -----------------------------------------------------------------

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Music Recommendation API"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_openapi_schema_generates(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/ratings/" in response.json()["paths"]


# --- songs / artists --------------------------------------------------------

def test_get_songs(client):
    response = client.get("/songs/")
    assert response.status_code == 200
    assert len(response.json()) == 6


def test_get_songs_pagination_is_bounded(client):
    assert len(client.get("/songs/?limit=2").json()) == 2
    assert len(client.get("/songs/?skip=5").json()) == 1
    assert client.get("/songs/?limit=1000").status_code == 422
    assert client.get("/songs/?skip=-1").status_code == 422


def test_song_not_found(client):
    assert client.get("/songs/99999").status_code == 404


def test_artist_not_found(client):
    assert client.get("/artists/99999").status_code == 404


def test_write_endpoints_require_auth(client):
    assert client.post("/artists/", json={"name": "X"}).status_code == 401
    assert client.post("/songs/", json={"title": "X"}).status_code == 401
    assert client.put("/songs/1", json={"title": "X"}).status_code == 401
    assert client.delete("/songs/1").status_code == 401
    assert client.delete("/artists/1").status_code == 401


def test_create_and_delete_song(client, auth_headers):
    artist = client.post(
        "/artists/", json={"name": "Test Artist", "genre": "pop"}, headers=auth_headers
    )
    assert artist.status_code == 201
    artist_id = artist.json()["id"]

    response = client.post(
        "/songs/",
        json={"title": "Test Song", "genre": "rock", "artist_id": artist_id},
        headers=auth_headers,
    )
    assert response.status_code == 201
    song_id = response.json()["id"]

    response = client.put(
        f"/songs/{song_id}", json={"popularity": 42}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["popularity"] == 42
    assert response.json()["title"] == "Test Song"

    assert client.delete(f"/songs/{song_id}", headers=auth_headers).status_code == 204
    assert client.get(f"/songs/{song_id}").status_code == 404
    client.delete(f"/artists/{artist_id}", headers=auth_headers)


def test_create_song_with_unknown_artist_is_rejected(client, auth_headers):
    response = client.post(
        "/songs/", json={"title": "Orphan", "artist_id": 9999}, headers=auth_headers
    )
    assert response.status_code == 400


def test_deleting_artist_cascades_to_songs(client, auth_headers):
    artist = client.post("/artists/", json={"name": "Cascade"}, headers=auth_headers)
    artist_id = artist.json()["id"]
    song = client.post(
        "/songs/",
        json={"title": "Cascade Song", "artist_id": artist_id},
        headers=auth_headers,
    )
    song_id = song.json()["id"]

    assert client.delete(f"/artists/{artist_id}", headers=auth_headers).status_code == 204
    assert client.get(f"/songs/{song_id}").status_code == 404


# --- auth -------------------------------------------------------------------

def test_register_login_and_me(client):
    response = client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "testpass123",
        },
    )
    assert response.status_code == 201
    assert "hashed_password" not in response.json()

    assert (
        client.post(
            "/auth/register",
            json={
                "username": "alice",
                "email": "other@example.com",
                "password": "testpass123",
            },
        ).status_code
        == 400
    )

    login = client.post(
        "/auth/login", data={"username": "alice", "password": "testpass123"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "alice"


def test_login_with_wrong_password(client, auth_headers):
    response = client.post(
        "/auth/login", data={"username": "pytest_user", "password": "wrong-password"}
    )
    assert response.status_code == 401


def test_invalid_token_is_rejected(client):
    assert (
        client.get("/auth/me", headers={"Authorization": "Bearer not-a-token"}).status_code
        == 401
    )


def test_rejects_weak_input(client):
    # Password too short
    assert (
        client.post(
            "/auth/register",
            json={"username": "bob", "email": "bob@example.com", "password": "short"},
        ).status_code
        == 422
    )
    # Invalid email
    assert (
        client.post(
            "/auth/register",
            json={"username": "carol", "email": "not-an-email", "password": "testpass123"},
        ).status_code
        == 422
    )


# --- ratings ----------------------------------------------------------------

def test_rating_flow(client, auth_headers):
    created = client.post(
        "/ratings/", json={"song_id": 1, "score": 5}, headers=auth_headers
    )
    assert created.status_code == 201
    assert created.json()["score"] == 5

    # Re-rating updates instead of duplicating.
    updated = client.post(
        "/ratings/", json={"song_id": 1, "score": 3.5}, headers=auth_headers
    )
    assert updated.status_code == 200
    assert updated.json()["id"] == created.json()["id"]

    mine = client.get("/ratings/me", headers=auth_headers)
    assert mine.status_code == 200
    assert len(mine.json()) == 1
    assert mine.json()[0]["score"] == 3.5

    assert (
        client.delete("/ratings/1", headers=auth_headers).status_code == 204
    )
    assert client.get("/ratings/me", headers=auth_headers).json() == []
    assert client.delete("/ratings/1", headers=auth_headers).status_code == 404


def test_rating_validation(client, auth_headers):
    assert (
        client.post("/ratings/", json={"song_id": 1, "score": 6}, headers=auth_headers).status_code
        == 422
    )
    assert (
        client.post("/ratings/", json={"song_id": 9999, "score": 4}, headers=auth_headers).status_code
        == 404
    )
    assert client.get("/ratings/me").status_code == 401


def test_deleting_song_removes_its_ratings(client, auth_headers):
    client.post("/ratings/", json={"song_id": 1, "score": 5}, headers=auth_headers)
    client.delete("/songs/1", headers=auth_headers)
    assert client.get("/ratings/me", headers=auth_headers).json() == []


# --- recommendations --------------------------------------------------------

def test_recommend_similar(client):
    response = client.get("/recommend/similar/1?limit=3")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert all(song["id"] != 1 for song in body)

    # Deterministic ordering.
    assert [song["id"] for song in body] == [
        song["id"] for song in client.get("/recommend/similar/1?limit=3").json()
    ]


def test_recommend_similar_unknown_song(client):
    assert client.get("/recommend/similar/9999").status_code == 404


def test_recommend_by_mood(client):
    assert client.get("/recommend/mood?mood=happy").status_code == 200
    assert client.get("/recommend/mood?mood=HAPPY").status_code == 200


def test_recommend_rejects_unknown_mood(client):
    response = client.get("/recommend/mood?mood=whatever")
    assert response.status_code == 400
    assert "happy" in response.json()["detail"]


def test_recommend_by_genre(client):
    assert client.get("/recommend/genre?genre=pop").status_code == 200
    assert client.get("/recommend/genre?genre=polka").status_code == 404


def test_for_me_requires_auth(client):
    assert client.get("/recommend/for-me").status_code == 401


def test_for_me_without_ratings_falls_back_to_popular(client, auth_headers):
    response = client.get("/recommend/for-me?limit=3", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert all("no rating history" in item["reason"] for item in body)
    scores = [item["score"] for item in body]
    assert scores == sorted(scores, reverse=True)


def test_for_me_uses_ratings_and_excludes_rated_songs(client, auth_headers):
    client.post("/ratings/", json={"song_id": 1, "score": 5}, headers=auth_headers)
    client.post("/ratings/", json={"song_id": 2, "score": 4}, headers=auth_headers)

    response = client.get("/recommend/for-me?limit=4", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()

    recommended_ids = [item["song"]["id"] for item in body]
    assert 1 not in recommended_ids
    assert 2 not in recommended_ids
    # The user only liked pop songs, so pop should rank first.
    assert body[0]["song"]["genre"] == "pop"
    assert "pop" in body[0]["reason"]

    scores = [item["score"] for item in body]
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= score <= 1 for score in scores)


# --- analytics --------------------------------------------------------------

def test_analytics_endpoints(client):
    trends = client.get("/analytics/genre-trends")
    assert trends.status_code == 200
    assert trends.json()[0]["count"] == 3  # three pop songs

    distribution = client.get("/analytics/mood-distribution")
    assert distribution.status_code == 200
    assert distribution.json()["total_songs"] == 6

    artists = client.get("/analytics/top-artists")
    assert artists.status_code == 200
    assert artists.json()[0]["artist"] == "Pop Artist"

    summary = client.get("/analytics/audio-features-summary")
    assert summary.status_code == 200
    assert 0 <= summary.json()["avg_energy"] <= 1


def test_analytics_on_empty_database_does_not_crash(empty_client):
    distribution = empty_client.get("/analytics/mood-distribution")
    assert distribution.status_code == 200
    assert distribution.json()["total_songs"] == 0
    assert distribution.json()["mood_breakdown"]["happy"]["percentage"] == 0
