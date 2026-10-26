"""Remove reproducible generated artifacts while preserving source and snapshots."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for pattern in ["assets/*.png", "reports/*.md", "reports/*.json", "projects/*/*.csv"]:
    for path in ROOT.glob(pattern):
        path.unlink()

