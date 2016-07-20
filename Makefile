# Watson

PYTHON ?= python
PIP ?= pip

VENV = virtualenv
VENV_ARGS = -p $(PYTHON)
VENV_DIR = $(CURDIR)/.venv

all: install

$(VENV_DIR): requirements-dev.txt
	$(VENV) $(VENV_ARGS) "$(VENV_DIR)"
	"$(VENV_DIR)"/bin/pip install -U setuptools wheel pip
	"$(VENV_DIR)"/bin/pip install -Ur $<

.PHONY: env
env: $(VENV_DIR)

.PHONY: install
install:
	$(PYTHON) setup.py install

.PHONY: install-dev
install-dev:
	$(PIP) install -r requirements-dev.txt
	$(PYTHON) setup.py develop

.PHONY: check
check: clean
	$(PYTHON) setup.py test

.PHONY: clean
clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d | xargs rm -fr

.PHONY: distclean
distclean: clean
	rm -fr *.egg *.egg-info/ .eggs/

.PHONY:
mostlyclean: clean distclean
	rm -rf "$(VENV_DIR)"

.PHONY: docs
docs: install-dev
	$(PYTHON) scripts/gen-cli-docs.py
	mkdocs build
