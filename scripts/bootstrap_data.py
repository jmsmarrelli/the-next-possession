"""Rebuild cached, analysis-ready portfolio data."""

from spurslab.data import bootstrap_data

if __name__ == "__main__":
    built = bootstrap_data()
    for name, frame in built.items():
        print(f"{name}: {len(frame):,} rows")

