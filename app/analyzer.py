from collections import Counter
from datetime import datetime, timezone


def build_digest(observations: list[dict]) -> dict:
    """Deterministic MVP analyzer; replace with VLM/CV adapters later."""
    now = datetime.now(timezone.utc)
    if not observations:
        return {
            "generated_at": now,
            "headline": "故乡还在等待第一次巡飞",
            "summary": "创建航线并上传第一组照片后，这里会出现故乡日报。",
            "highlights": [],
        }

    places = {x["place_name"] for x in observations}
    counts: Counter[str] = Counter()
    for item in observations:
        counts.update(item.get("object_counts", {}))
    highlights = [f"记录了 {len(observations)} 个画面，覆盖 {len(places)} 个地点"]
    highlights.extend(f"识别到 {name} {count} 个" for name, count in counts.most_common(3))
    return {
        "generated_at": now,
        "headline": f"今天，故乡的 {len(places)} 个地方有了新记录",
        "summary": "本次固定路线采集已归档。随着同一观察点持续积累，系统会生成季节变化和多年延时影像。",
        "highlights": highlights,
    }
