SPHINX_BUILDDIR = docs/_build

all: install

install:
	python setup.py install

install-dev:
	pip install -r requirements-dev.txt
	python setup.py develop

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d | xargs rm -fr

distclean: clean
	rm -fr *.egg *.egg-info/

docs: install-dev
	python scripts/gen-cli-docs.py
	sphinx-build -a -n -b html -d $(SPHINX_BUILDDIR)/doctrees docs $(SPHINX_BUILDDIR)/html
