"""Run all portfolio analyses."""

import json

from spurslab.projects import run_all

if __name__ == "__main__":
    print(json.dumps(run_all(), indent=2))

