"""Python entry point: Wembanyama availability impact."""

from spurslab.config import Paths
from spurslab.projects import run_wemby

if __name__ == "__main__":
    print(run_wemby(Paths()))

