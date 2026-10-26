"""Python entry point: leaguewide player archetypes."""

from spurslab.config import Paths
from spurslab.projects import run_archetypes

if __name__ == "__main__":
    print(run_archetypes(Paths()))

