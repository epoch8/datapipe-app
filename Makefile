build-example:
	docker build 

build-frontend:
	docker run --rm -v `pwd`/frontend:/app -v `pwd`/datapipe_app/frontend:/app/build -w /app node:18.7.0-slim yarn
	docker run --rm -v `pwd`/frontend:/app -v `pwd`/datapipe_app/frontend:/app/build -w /app node:18.7.0-slim yarn build

build: build-frontend
	poetry build

lint:
	flake8 datapipe_app
    mypy -p datapipe_app --ignore-missing-imports --follow-imports=silent --namespace-packages
