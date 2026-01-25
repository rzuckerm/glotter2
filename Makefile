PACKAGE := glotter
TESTS := test
CONFIG_FILE = pyproject.toml
ALL = $(PACKAGE) $(TESTS)
UV_VERSION = $(shell sed -nr 's/uv-version: "([^"]+)"/\1/p' repo-config.yml)

SHELL := bash

VENV := .venv

UV := uv
RUN := $(UV) run
META := .meta
META_INSTALL := $(META)/.install

PYTEST_ARGS ?= -vvl \
	--color=yes \
	--cov=$(PACKAGE) \
	--cov-branch \
	--cov-report term-missing \
	--cov-report=html:$(META)/html_cov/ \
	--cov-report=xml:$(META)/coverage.xml

help:
	@echo "build          - Build package"
	@echo "clean          - Delete output files"
	@echo "coverage-badge - Make coverage badge"
	@echo "doc            - Make documentation"
	@echo "fix            - Format code and fix linting errors with ruff"
	@echo "format         - Format code with ruff"
	@echo "lint           - Lint code with ruff"
	@echo "test           - Run unit tests with pytest."
	@echo "                 Use PYTEST_ARGS to override options"

$(META):
	mkdir -p $@

$(META_INSTALL): $(CONFIG_FILE) | $(META)
	$(UV) sync
	touch $@

.PHONY: build
build:
	@echo "** Building package ***"
	rm -rf dist
	$(UV) build
	@echo ""

.PHONY: clean
clean:
	rm -rf $(PACKAGE)/__pycache__/ \
		$(TESTS)/__pycache__/ \
		$(META)/ \
		.pytest_cache/ \
		.ruff_cache/ \
		dist \
		$(VENV)
	rm -f .coverage .coverage.*

.PHONY: coverage-badge
coverage-badge:
	echo "*** Creating code coverage badge ***"
	rm -f $(META)/html_cov/.gitignore $(META)/html_cov/badge.svg
	[ -f .coverage ]
	$(RUN) genbadge coverage -i $(META)/coverage.xml -o $(META)/html_cov/badge.svg
	@echo ""

.PHONY: doc
doc: $(META_INSTALL)
	@echo "*** Building docs ***"
	$(RUN) sphinx-build -b html doc $(META)/doc
	@echo ""

.PHONY: fix
fix: $(META_INSTALL) format
	@echo "*** Fixing with ruff ***"
	$(RUN) ruff check --fix $(ALL)

.PHONY: format
format: $(META_INSTALL)
	@echo "*** Formatting with ruff ***"
	$(RUN) ruff format $(ALL)
	@echo ""

.PHONY: lint
lint:
	@echo "*** Linting with ruff ***"
	$(RUN) ruff format --check $(ALL)
	$(RUN) ruff check $(ALL)
	@echo ""

.PHONY: test
test: $(META_INSTALL)
	@echo "*** Running tests ***"
	$(RUN) pytest $(PYTEST_ARGS)
	@echo ""
