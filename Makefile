# -- General
SHELL := /bin/bash

# ==============================================================================
# RULES

default: help

# -- Build
bootstrap: ## bootstrap the project for development
bootstrap: \
  build
.PHONY: bootstrap

build: ## install project
	uv sync --locked --all-extras --dev
.PHONY: build

docs-serve: ## run documentation server 
	uv run mkdocs serve -w docs
.PHONY: docs-serve

docs-publish: ## publish documentation
	uv run mkdocs gh-deploy --force
.PHONY: docs-publish

test: ## run tests
	uv run pytest
.PHONY: test

completion-scripts:
	scripts/create-completion-script.sh bash
	scripts/create-completion-script.sh zsh
.PHONY: completion-scripts

# -- Misc
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help
