# Music Recommendation API

A data-driven RESTful API for music discovery and personalised recommendations,
built with FastAPI and SQLite.

## Tech stack

| Layer | Choice |
| --- | --- |
| Framework | FastAPI |
| Database | SQLite via SQLAlchemy 2.x ORM |
| Auth | JWT (PyJWT) + bcrypt password hashing |
| Dataset | Spotify Tracks Dataset (Kaggle) |

## Project layout

```
app/
  main.py            # FastAPI app + startup (table creation)
  config.py          # settings from environment variables
  database.py        # engine, session, get_db dependency
  auth/              # JWT + password hashing
  models/            # User, Artist, Song, Rating
  schemas/           # Pydantic request/response models
  routers/           # auth, songs, artists, ratings, recommend, analytics
  services/          # content-based recommender
tests/               # API tests (isolated temp database)
data/                # dataset importer (+ dataset.csv, not committed)
docs/                # Swagger UI PDF, slides, technical report
```

## Setup

```bash
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate
pip install -r requirements.txt
```

Optional: load the demo data (needs the Kaggle CSV placed at `data/dataset.csv`).

```bash
python data/import_spotify.py            # imports the first 5000 rows
python data/import_spotify.py data/dataset.csv 2000
```

The database file `music.db` is created automatically on first startup. It is
git-ignored; regenerate it with the import script above.

## Configure

All settings have development defaults and can be overridden with environment
variables. Copy `.env.example` to `.env` and edit it (loaded automatically when
`python-dotenv` is installed), or export the variables in your shell:

| Variable | Default | Purpose |
| --- | --- | --- |
| `MRA_SECRET_KEY` | dev key | JWT signing key - **set this in production** |
| `MRA_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token lifetime |
| `MRA_DATABASE_URL` | `sqlite:///./music.db` | SQLAlchemy URL |
| `MRA_PAGE_SIZE_DEFAULT` / `MRA_PAGE_SIZE_MAX` | `20` / `100` | List pagination |
| `MRA_RECOMMEND_LIMIT_DEFAULT` / `MRA_RECOMMEND_LIMIT_MAX` | `10` / `50` | Recommendation size |
| `MRA_MAX_SIMILAR_CANDIDATES` | `5000` | Songs scanned per recommendation request |

If `MRA_SECRET_KEY` is left at its default, the app logs a warning at startup.

## Run

```bash
uvicorn app.main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- API docs PDF: `docs/Music Recommendation API - Swagger UI.pdf`
- Slides: `docs/Music_Recommendation_API.pptx`
- Technical report: `docs/technical_report.pdf`

## Authentication

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"testpass123"}'

curl -X POST http://127.0.0.1:8000/auth/login \
  -d "username=alice&password=testpass123"
```

Send the returned token as `Authorization: Bearer <token>`.

## Endpoints

### Auth

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/auth/register` | - | Create an account |
| POST | `/auth/login` | - | Get a JWT access token |
| GET | `/auth/me` | yes | Current user |

### Catalogue

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/songs/` | - | List songs (`skip`, `limit`) |
| GET | `/songs/{id}` | - | Song detail |
| POST | `/songs/` | yes | Create a song |
| PUT | `/songs/{id}` | yes | Update a song |
| DELETE | `/songs/{id}` | yes | Delete a song (and its ratings) |
| GET | `/artists/` | - | List artists |
| GET | `/artists/{id}` | - | Artist detail |
| POST | `/artists/` | yes | Create an artist |
| PUT | `/artists/{id}` | yes | Update an artist |
| DELETE | `/artists/{id}` | yes | Delete an artist (and its songs) |

### Ratings

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/ratings/` | yes | Rate a song (1-5). Re-rating updates, returns 200 |
| GET | `/ratings/me` | yes | My ratings |
| DELETE | `/ratings/{song_id}` | yes | Remove my rating |

### Recommendations

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/recommend/similar/{song_id}` | - | Content-similar songs |
| GET | `/recommend/mood?mood=happy` | - | happy, sad, energetic, calm (400 otherwise) |
| GET | `/recommend/genre?genre=pop` | - | Songs in a genre, most popular first |
| GET | `/recommend/for-me` | yes | Personalised mix based on my ratings |

### Analytics

| Method | Path | Description |
| --- | --- | --- |
| GET | `/analytics/genre-trends` | Top genres by song count |
| GET | `/analytics/mood-distribution` | Mood buckets + percentages (safe on an empty DB) |
| GET | `/analytics/top-artists` | Artists ranked by average popularity |
| GET | `/analytics/audio-features-summary` | Average audio features |

## How recommendations work

- **Similar songs**: cosine similarity over `danceability`, `energy`,
  `valence`, `tempo` (scaled to 0-1), `acousticness`, `speechiness`.
- **For me**: builds a weighted taste profile from the user's ratings
  (`score - 2.5`), then ranks unrated songs with 75% audio similarity and 25%
  genre preference. Users without ratings get popular songs, with
  `reason` explaining the fallback.

Every ranking is deterministic: candidates are ordered by `id` before scoring.

## Tests

```bash
pytest -q
```

Tests use a temporary SQLite database per test (dependency override), so the
real `music.db` is never touched.

## Limitations

- Content-based only; no collaborative filtering / matrix factorisation.
- No refresh tokens, token revocation, or login rate limiting.
- No Alembic migrations; schema changes require recreating `music.db`.
- `CORS` is wide open (`*`) for local development.
