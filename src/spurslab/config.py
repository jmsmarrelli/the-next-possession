"""Configuration and filesystem helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Paths:
    root: Path = ROOT

    @property
    def config(self) -> Path:
        return self.root / "config"

    @property
    def raw(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def processed(self) -> Path:
        return self.root / "data" / "processed"

    @property
    def snapshots(self) -> Path:
        return self.root / "data" / "snapshots"

    @property
    def reports(self) -> Path:
        return self.root / "reports"

    @property
    def assets(self) -> Path:
        return self.root / "assets"

    @property
    def docs(self) -> Path:
        return self.root / "docs"

    def ensure(self) -> None:
        for path in (self.raw, self.processed, self.snapshots, self.reports, self.assets, self.docs):
            path.mkdir(parents=True, exist_ok=True)


def load_settings(path: Path | None = None) -> dict[str, Any]:
    settings_path = path or ROOT / "config" / "settings.yml"
    with settings_path.open(encoding="utf-8") as handle:
        return cast(dict[str, Any], yaml.safe_load(handle))
