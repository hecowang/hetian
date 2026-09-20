import io

from fastapi.testclient import TestClient

from app.main import app


def test_mission_and_observation(tmp_path, monkeypatch):
    import app.store as store
    import app.main as main

    monkeypatch.setattr(store, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(store, "MEDIA_DIR", tmp_path / "media")
    monkeypatch.setattr(main, "MEDIA_DIR", tmp_path / "media")
    with TestClient(app) as client:
        mission = client.post("/api/missions", json={"route_name": "一号线"})
        assert mission.status_code == 201
        result = client.post(
            "/api/observations",
            data={"mission_id": mission.json()["id"], "place_id": "tree", "place_name": "门前的树", "latitude": 1, "longitude": 2, "altitude_m": 20, "object_counts": '{"tree":1}'},
            files={"image": ("tree.jpg", io.BytesIO(b"image"), "image/jpeg")},
        )
        assert result.status_code == 201
        assert client.get("/api/timeline").json()[0]["place_name"] == "门前的树"
