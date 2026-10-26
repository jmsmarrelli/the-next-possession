"""Python entry point: 2026 Finals clutch autopsy."""

from spurslab.config import Paths
from spurslab.projects import run_finals

if __name__ == "__main__":
    print(run_finals(Paths()))

