all: check test

check:
	python -m mypy *.py mdl/*.py mdl/mcl/*.py

test:
	python test.py
	
freeze:
	pip freeze --local > requirements.txt

docs:
	python -m mdl README.mdl --write-markdown README.md
