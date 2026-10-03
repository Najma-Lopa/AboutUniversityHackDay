import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "universities.json"


def load_universities():
    """
    Load saved universities safely.
    """

    if not DATA_FILE.exists():
        return {}

    try:

        data = json.loads(
            DATA_FILE.read_text(
                encoding="utf-8"
            )
        )

        return data if isinstance(data, dict) else {}

    except Exception:
        return {}


def save_universities(data):
    """
    Save universities safely.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    DATA_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )