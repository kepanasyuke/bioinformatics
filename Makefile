PYTHON ?= python

PROJECTS := 01_wgs_pipeline 02_regression 03_toolchain 04_cluster_budget 05_rnaseq 06_legacy 07_freqdb

.PHONY: all lint test coverage reports headers game clean

all: lint test reports headers

lint:
	$(PYTHON) tools/check_style.py .

test:
	$(PYTHON) tools/run_tests.py

coverage:
	$(PYTHON) tools/coverage.py

reports:
	$(PYTHON) projects/01_wgs_pipeline/src/wgs_pipeline.py
	$(PYTHON) projects/02_regression/src/regression.py
	$(PYTHON) projects/03_toolchain/src/toolchain.py
	$(PYTHON) projects/04_cluster_budget/src/budget.py
	$(PYTHON) projects/05_rnaseq/src/rnaseq.py
	$(PYTHON) projects/06_legacy/src/legacy.py
	$(PYTHON) projects/07_freqdb/src/freqdb.py

headers:
	$(PYTHON) -m tools.viz.header

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +
