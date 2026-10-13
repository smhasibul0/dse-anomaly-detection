"""Where data lives. Set PROJECT_DATA_DIR (e.g. a Google Drive folder on Colab)
to keep data outside the repo; otherwise it defaults to <repo>/data."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("PROJECT_DATA_DIR", ROOT / "data"))
RAW, INTERIM, PROCESSED = DATA / "raw", DATA / "interim", DATA / "processed"
