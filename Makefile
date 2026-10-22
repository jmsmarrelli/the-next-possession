.PHONY: install data build test r-test parity lint verify render render-fallback clean

PYTHON ?= python3

install:
	$(PYTHON) -m pip install -e ".[dev,notebooks]"

data:
	$(PYTHON) scripts/bootstrap_data.py

build:
	$(PYTHON) scripts/build_all.py

test:
	$(PYTHON) -m pytest

r-test:
	Rscript -e 'source(file.path("R", "bootstrap.R")); testthat::test_dir(file.path("R", "spurslabR", "tests", "testthat"), env = globalenv(), reporter = "summary")'

parity:
	$(PYTHON) scripts/verify_r_parity.py

lint:
	$(PYTHON) -m ruff check src scripts projects tests

verify: lint test r-test parity

render: build
	quarto render

render-fallback: build
	$(PYTHON) scripts/render_fallback.py

clean:
	$(PYTHON) scripts/clean_generated.py
