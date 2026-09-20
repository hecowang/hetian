"""Send a tiny two-stop simulated flight to a running local server."""
import json
import urllib.request
from datetime import datetime, timezone

BASE = "http://127.0.0.1:8000"


def post_json(path: str, payload: dict) -> dict:
    req = urllib.request.Request(BASE + path, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())


def svg(place: str, color: str) -> bytes:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800"><rect width="1200" height="800" fill="{color}"/><circle cx="930" cy="150" r="70" fill="#f3d38a"/><path d="M0 580 Q300 400 600 570 T1200 510 V800 H0Z" fill="#708b5b"/><text x="60" y="100" font-size="52" fill="#fff">{place}</text></svg>'''.encode()


def upload(mission_id: int, place_id: str, name: str, color: str, counts: dict):
    boundary = "----hometownkeeper"
    fields = {"mission_id": str(mission_id), "place_id": place_id, "place_name": name, "latitude": "31.352", "longitude": "118.433", "altitude_m": "42", "captured_at": datetime.now(timezone.utc).isoformat(), "note": "模拟固定航点拍摄", "object_counts": json.dumps(counts)}
    body = bytearray()
    for key, value in fields.items():
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n".encode()
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{place_id}.svg\"\r\nContent-Type: image/svg+xml\r\n\r\n".encode() + svg(name, color) + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(BASE + "/api/observations", body, {"Content-Type": f"multipart/form-data; boundary={boundary}"})
    return json.loads(urllib.request.urlopen(req).read())


if __name__ == "__main__":
    mission = post_json("/api/missions", {"route_name": "故乡一号线", "drone_id": "simulator-01"})
    upload(mission["id"], "old-house", "老房子", "#9cb5c3", {"house": 1, "tree": 3})
    upload(mission["id"], "village-field", "村口田野", "#b9c9d5", {"field": 4, "person": 2})
    print(f"Mission {mission['id']} uploaded. Open {BASE}")
