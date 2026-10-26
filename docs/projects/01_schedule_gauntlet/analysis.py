"""Python entry point: 2026-27 schedule gauntlet."""

from spurslab.config import Paths
from spurslab.projects import run_schedule

if __name__ == "__main__":
    print(run_schedule(Paths()))

