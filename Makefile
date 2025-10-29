PYTHON ?= python

.PHONY: install install-dev lint test test-integration smoke

install:
	$(PYTHON) -m pip install -r requirements.txt

install-dev:
	$(PYTHON) -m pip install -r requirements-dev.txt

lint:
	flake8 .

test:
	$(PYTHON) -m unittest discover -v

test-integration:
	$(PYTHON) -m unittest tests.test_integration_hardware -v

smoke:
	$(PYTHON) -m src.main
