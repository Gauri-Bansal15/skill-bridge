import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def read(kind: str, name: str) -> str:
    return (ROOT / "data" / kind / name).read_text(encoding="utf-8")
