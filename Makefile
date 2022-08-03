build-example:
	docker build 

build-frontend:
	docker run --rm -v `pwd`/frontend:/app -v `pwd`/datapipe_app/frontend:/app/build -w /app node:18.7.0-slim yarn
	docker run --rm -v `pwd`/frontend:/app -v `pwd`/datapipe_app/frontend:/app/build -w /app node:18.7.0-slim yarn build

build: build-frontend
	poetry build
