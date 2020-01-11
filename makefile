all: check test

check:
	python -m mypy *.py
.PHONY: check

test:
	python test.py
	python -m pytest test/*.py
.PHONY: test
	
freeze:
	pip freeze --local > requirements.txt

docs:
	python -m mdl README.mdl --write-markdown README.md
.PHONY: docs
