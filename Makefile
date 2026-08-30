.PHONY: setup test reanalysis

setup:
	pip install -r requirements.txt

test:
	pytest tests/ -v

reanalysis:
	python -m src.experimentation.run_reanalysis
