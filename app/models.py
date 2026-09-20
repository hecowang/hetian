from datetime import datetime

from pydantic import BaseModel, Field


class MissionCreate(BaseModel):
    route_name: str = Field(min_length=1, max_length=100)
    drone_id: str = Field(default="simulator-01", max_length=100)


class Mission(BaseModel):
    id: int
    route_name: str
    drone_id: str
    started_at: datetime
    status: str


class Observation(BaseModel):
    id: int
    mission_id: int
    place_id: str
    place_name: str
    captured_at: datetime
    latitude: float
    longitude: float
    altitude_m: float
    media_url: str
    note: str = ""
    object_counts: dict[str, int] = {}


class Digest(BaseModel):
    generated_at: datetime
    headline: str
    summary: str
    highlights: list[str]
