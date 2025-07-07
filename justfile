@default:
	just --list
	
all: mypy test

mypy:
	python -m mypy *.py mdl/*.py mdl/mcl/*.py

test:
	python test.py
	
freeze:
	pip freeze --local > requirements.txt

docs:
	python -m mdl README.mdl --write markdown README.md

setup-dev:
	python3.12 -m venv py_env
	py_env/bin/pip install -r requirements.txt
