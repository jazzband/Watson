# Watson

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
	mkdocs build

ghp-setup:
	if [[ -z `git config user.name` && $(GH_USER_NAME) ]] ; then git config user.name $(GH_USER_NAME) ; fi
	if [[ -z `git config user.email` && $(GH_USER_EMAIL) ]] ; then git config user.email $(GH_USER_EMAIL) ; fi
	if [[ $(GH_TOKEN) && $(GH_REF) ]] ; then git remote add upstream "https://$(GH_TOKEN)@$(GH_REF)" ; fi

gh-deploy: docs ghp-setup
	mkdocs gh-deploy -r upstream
	git log -n 2 upstream/gh-pages
