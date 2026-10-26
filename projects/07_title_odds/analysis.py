"""Python entry point: schedule and title simulations."""

from spurslab.config import Paths
from spurslab.projects import run_title_odds

if __name__ == "__main__":
    print(run_title_odds(Paths()))

