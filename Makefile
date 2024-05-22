PACKAGE := glotter
TESTS := test
CONFIG_FILE = pyproject.toml
ALL = $(PACKAGE) $(TESTS)

SHELL := bash

VENV := venv

ifeq ($(OS),Windows_NT)
	ifneq ($(GITHUB_PATH),)
		ACT :=
		CREATE_VIRTUALENV :=
		POETRY := /c/Users/runneradmin/.local/venv/Scripts/poetry.exe
	else
		ACT := $(VENV)/bin/activate
	endif
else
	ifneq ($(GITHUB_PATH),)
		ACT :=
		CREATE_VIRTUALENV :=
		POETRY:= poetry
	else
		ACT := source $(VENV)/bin/activate &&
		CREATE_VIRTUALENV := if ! virtualenv -p python3.8 $(VENV) 2>/dev/null; then python -m venv $(VENV); fi
		POETRY := $(ACT) poetry
	endif
endif

RUN := $(POETRY) run
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
	@echo "format         - Format code with black"
	@echo "lint           - Lint code with black and pylint"
	@echo "lint-black     - Lint code with black"
	@echo "lint-pylint    - Lint code with pylint"
	@echo "test           - Run unit tests with pytest."
	@echo "                 Use PYTEST_ARGS to override options"

ifneq ($(GITHUB_PATH),)
$(META):
	mkdir -p $@
else
$(META): | $(VENV)
	mkdir -p $@

$(VENV):
	@echo "*** Initializing environment ***"
	$(CREATE_VIRTUALENV)
	$(ACT) pip install 'poetry==1.8.3'
	@echo ""
endif

$(META_INSTALL): $(CONFIG_FILE) | $(META)
	$(POETRY) install
	touch $@

.PHONY: build
build:
	@echo "** Building package ***"
	rm -rf dist
	$(POETRY) build
	@echo ""

.PHONY: clean
clean:
	rm -rf $(PACKAGE)/__pycache__/ \
		$(TESTS)/__pycache__/ \
		$(META)/ \
		.pytest_cache/ \
		dist \
		venv
	rm -f .coverage .coverage.*

.PHONY: coverage-badge
coverage-badge:
	echo "*** Creating code coverage badge ***"
	rm -f $(META)/html_cov/.gitignore $(META)/html_cov/badge.svg
	[ -f .coverage ]
	$(RUN) coverage-badge -o $(META)/html_cov/badge.svg
	echo ""

.PHONY: doc
doc: $(META_INSTALL)
	@echo "*** Building docs ***"
	$(RUN) sphinx-build -b html doc $(META)/doc
	@echo ""

.PHONY: format
format: $(META_INSTALL)
	$(RUN) black $(ALL)

.PHONY: lint
lint: lint-black lint-pylint

.PHONY: lint-black
lint-black: $(META_INSTALL)
	@echo "*** Linting with black ***"
	$(RUN) black --check $(ALL)
	@echo ""

.PHONY: lint-pylint
lint-pylint: $(META_INSTALL)
	@echo "*** Linting with pylint ***"
	$(RUN) pylint --rcfile $(CONFIG_FILE) $(PACKAGE)
	$(RUN) pylint --rcfile $(TESTS)/$(CONFIG_FILE) $(TESTS)
	@echo ""

.PHONY: test
test: $(META_INSTALL)
	@echo "*** Running tests ***"
	$(RUN) pytest $(PYTEST_ARGS)
	@echo ""
