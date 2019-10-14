all: check test

check:
	mypy mdl.py
.PHONY: check

test:
	python test.py
	python -m pytest test/*.py
.PHONY: test
	
freeze:
	pip freeze --local > requirements.txt
