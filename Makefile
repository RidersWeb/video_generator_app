.PHONY: run install

run:
	uvicorn app.main:app --reload

install:
	pip install -r requirements.txt

kill:
	lsof -t -i :8000 | xargs kill -9
