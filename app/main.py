import json
import shutil
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .analyzer import build_digest
from .models import Digest, Mission, MissionCreate, Observation
from .store import MEDIA_DIR, ROOT, connect, init_db, row_to_observation


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="故乡守望", version="0.1.0", lifespan=lifespan)
app.mount("/media", StaticFiles(directory=MEDIA_DIR, check_dir=False), name="media")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(ROOT / "app" / "static" / "index.html")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/api/missions", response_model=Mission, status_code=201)
def create_mission(payload: MissionCreate):
    started_at = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        cur = db.execute(
            "INSERT INTO missions(route_name, drone_id, started_at, status) VALUES (?, ?, ?, ?)",
            (payload.route_name, payload.drone_id, started_at, "collecting"),
        )
        mission_id = cur.lastrowid
    return {"id": mission_id, **payload.model_dump(), "started_at": started_at, "status": "collecting"}


@app.post("/api/observations", response_model=Observation, status_code=201)
def create_observation(
    mission_id: int = Form(...),
    place_id: str = Form(...),
    place_name: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    altitude_m: float = Form(...),
    captured_at: datetime | None = Form(None),
    note: str = Form(""),
    object_counts: str = Form("{}"),
    image: UploadFile = File(...),
):
    try:
        counts = json.loads(object_counts)
        if not isinstance(counts, dict):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(400, "object_counts must be a JSON object")
    with connect() as db:
        if not db.execute("SELECT 1 FROM missions WHERE id = ?", (mission_id,)).fetchone():
            raise HTTPException(404, "mission not found")
        suffix = Path(image.filename or "capture.jpg").suffix.lower() or ".jpg"
        filename = f"{uuid4().hex}{suffix}"
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        with (MEDIA_DIR / filename).open("wb") as target:
            shutil.copyfileobj(image.file, target)
        timestamp = (captured_at or datetime.now(timezone.utc)).isoformat()
        cur = db.execute(
            """INSERT INTO observations
            (mission_id, place_id, place_name, captured_at, latitude, longitude,
             altitude_m, media_url, note, object_counts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (mission_id, place_id, place_name, timestamp, latitude, longitude,
             altitude_m, f"/media/{filename}", note, json.dumps(counts, ensure_ascii=False)),
        )
        row = db.execute("SELECT * FROM observations WHERE id = ?", (cur.lastrowid,)).fetchone()
    return row_to_observation(row)


@app.get("/api/timeline", response_model=list[Observation])
def timeline(limit: int = 100):
    with connect() as db:
        rows = db.execute(
            "SELECT * FROM observations ORDER BY captured_at DESC LIMIT ?", (min(limit, 500),)
        ).fetchall()
    return [row_to_observation(row) for row in rows]


@app.get("/api/places/{place_id}/compare")
def compare(place_id: str):
    with connect() as db:
        rows = db.execute(
            "SELECT * FROM observations WHERE place_id = ? ORDER BY captured_at DESC LIMIT 2",
            (place_id,),
        ).fetchall()
    if len(rows) < 2:
        raise HTTPException(404, "this place needs at least two observations")
    latest, previous = map(row_to_observation, rows)
    keys = set(latest["object_counts"]) | set(previous["object_counts"])
    changes = {k: latest["object_counts"].get(k, 0) - previous["object_counts"].get(k, 0) for k in keys}
    return {"place_id": place_id, "previous": previous, "latest": latest, "count_changes": changes}


@app.get("/api/digest/latest", response_model=Digest)
def latest_digest():
    return build_digest(timeline(30))
