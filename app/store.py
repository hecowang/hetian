import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MEDIA_DIR = DATA_DIR / "media"
DB_PATH = DATA_DIR / "hometown.db"


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    MEDIA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS missions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              route_name TEXT NOT NULL,
              drone_id TEXT NOT NULL,
              started_at TEXT NOT NULL,
              status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS observations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              mission_id INTEGER NOT NULL REFERENCES missions(id),
              place_id TEXT NOT NULL,
              place_name TEXT NOT NULL,
              captured_at TEXT NOT NULL,
              latitude REAL NOT NULL,
              longitude REAL NOT NULL,
              altitude_m REAL NOT NULL,
              media_url TEXT NOT NULL,
              note TEXT NOT NULL DEFAULT '',
              object_counts TEXT NOT NULL DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_observation_place_time
              ON observations(place_id, captured_at DESC);
            """
        )


def row_to_observation(row: sqlite3.Row) -> dict:
    item = dict(row)
    item["object_counts"] = json.loads(item["object_counts"])
    return item
