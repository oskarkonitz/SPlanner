import json
from pathlib import Path

DEFAULT_DATA = {
    "settings": {
        "max_per_day": 2,
        "max_same_subject_per_day": 1,
    },
    "exams": []
}

def load(path="storage.json"):
    p = Path(path)
    if not p.exists():
        return DEFAULT_DATA.copy()
    return json.loads(p.read_text(encoding="utf-8"))

def save(data, path="storage.json"):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")