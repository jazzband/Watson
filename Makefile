# Watson

# git repository setup
# (used to automate travis-ci gh-pages deploy)
ifndef ($(git config user.name))
	ifdef $(GH_USER_NAME)
		git config user.name $(GH_USER_NAME)
	endif
endif

ifndef ($(git config user.email))
	ifdef $(GH_USER_EMAIL)
		git config user.email $(GH_USER_EMAIL)
	endif
endif

ifdef ($(GH_TOKEN))
	ifdef ($(GH_REF))
		git remote add upstream "https://$(GH_TOKEN)@$(GH_REF)"
	endif
endif

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

gh-deploy: docs
	mkdocs gh-deploy -r upstream
	git log -n 2 upstream/gh-pages
