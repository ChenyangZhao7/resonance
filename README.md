# Music Recommendation API

A data-driven RESTful API for music discovery and personalised recommendations,
built with FastAPI and SQLite.

## Tech Stack
- **Framework**: FastAPI (Python)
- **Database**: SQLite via SQLAlchemy ORM
- **Auth**: JWT (JSON Web Tokens)
- **Dataset**: Spotify Tracks Dataset (Kaggle)

## Setup Instructions

### 1. Clone the repository
git clone https://github.com/sc22cz/music-recommendation-api.git
cd music-recommendation-api

### 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Run the API
uvicorn app.main:app --reload

### 5. View API docs
Open http://127.0.0.1:8000/docs in your browser

## API Documentation
See /docs/api_docs.pdf

## Links
- GitHub: https://github.com/sc22cz/music-recommendation-api