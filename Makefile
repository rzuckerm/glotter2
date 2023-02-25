PACKAGE := glotter
TESTS := test
CONFIG_FILE = pyproject.toml
ALL = $(PACKAGE) $(TESTS)

SHELL := bash
POETRY := source venv/bin/activate && poetry

RUN := $(POETRY) run
META := .meta
META_INSTALL := $(META)/.install
VENV := venv

PYTEST_ARGS ?= -vvl \
	--color=yes \
	--cov=$(PACKAGE) \
	--cov-branch \
	--cov-report term-missing \
	--cov-report=html:$(META)/html_cov/ \
	--cov-report=xml:$(META)/coverage.xml

help:
	@echo "clean       - Delete output files"
	@echo "format      - Format code with black"
	@echo "lint        - Lint code with black and pylint"
	@echo "lint-black  - Lint code with black"
	@echo "lint-pylint - Lint code with pylint"
	@echo "test        - Run unit tests with pytest."
	@echo "              Use PYTEST_ARGS to override options"

$(META): | $(VENV)
	mkdir -p $@

$(VENV):
	@echo "*** Initializing environment ***"
	virtualenv -p python3.8 venv
	venv/bin/pip install 'poetry>=1.3.2,<1.4.0'
	@echo ""

$(META_INSTALL): $(CONFIG_FILE) | $(META)
	$(POETRY) install
	touch $@

.PHONY: clean
clean:
	rm -rf $(PACKAGE)/__pycache__/ \
		$(TESTS)/__pycache__/ \
		$(META)/ \
		.pytest_cache/ \
		dist
	rm -f .coverage .coverage.*

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
	@echo ""

.PHONY: test
test: $(META_INSTALL)
	@echo "*** Running tests ***"
	$(RUN) pytest $(PYTEST_ARGS)
	@echo ""
