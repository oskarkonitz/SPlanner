import json
from pathlib import Path

# domyslne dane do zapisania w pliku storage.json jesli dopiero sie go tworzy
DEFAULT_DATA = {
    "settings": {
        "max_per_day": 2,
        "max_same_subject_per_day": 1,
        "lang": "en"
    },
    "exams": [],
    "topics": []
}

#   FUNKCJA WCZYTUJACA BAZE DANYCH PROGRAMU
def load(path="storage.json"):
    p = Path(path)
    if not p.exists():
        return DEFAULT_DATA.copy()
    return json.loads(p.read_text(encoding="utf-8"))

#   FUNKCJA ZAPISUJACA DANE Z PROGRAMU DO BAZY DANYCH
def save(data, path="storage.json"):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

#   FUNKCJA WCZYTUJACA JEZYK W JAKIM PROGRAM MA ZOSTAC WYSWIETLONY
def load_language(lang_code="en"):
    folder = Path("languages")
    file_path = folder / f"lang_{lang_code}.json"

    if file_path.exists():
        return json.loads(file_path.read_text(encoding="utf-8"))

    # awaryjnie jesli funkcja dostanie nieistniejacy kod jezyka to ustawi domyslnie angielski
    alternative_path = folder / "lang_en.json"
    if alternative_path.exists():
        return json.loads(alternative_path.read_text(encoding="utf-8"))

    # jesli brakuje danych jezykowy to zwroci puste dany zeby program sie nie wywalil
    return {}
