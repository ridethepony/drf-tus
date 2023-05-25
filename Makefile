.DEFAULT_GOAL := help
define BROWSER_PYSCRIPT
import os, webbrowser, sys
from urllib.request import pathname2url
webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT
BROWSER := python -c "$$BROWSER_PYSCRIPT"

clean: clean-build clean-pyc

.PHONY: clean-build
clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

.PHONY: clean-pyc
clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

.PHONY: flaketest
flaketest:
	flake8

.PHONY: coveragetest
coveragetest:
	coverage run -m unittest --catch tests

.PHONY: coverage
coverage: coveragetest
	coverage html
	@echo "Coverage report is located at ./var/htmlcov/index.html"

.PHONY: migrationtest
migrationtest:
	# Check if there are any model changes without migrations
	./manage.py makemigrations --dry-run --no-input --check --settings tests.test_settings

.PHONY: docs
docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/drf-tus.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ rest_framework_tus
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

release: clean ## package and upload a release
	python setup.py sdist upload
	python setup.py bdist_wheel upload

sdist: clean ## package
	python setup.py sdist
	ls -l dist

##
# These targets are to be used by GitHub actions
##

.PHONY: install-pipeline
install-pipeline:
	pip install . -r requirements_local.txt
