"""Python entry point: contender landscape."""

from spurslab.config import Paths
from spurslab.projects import run_contenders

if __name__ == "__main__":
    print(run_contenders(Paths()))

