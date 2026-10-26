"""Python entry point: rotation chemistry proxies."""

from spurslab.config import Paths
from spurslab.projects import run_rotation

if __name__ == "__main__":
    print(run_rotation(Paths()))

