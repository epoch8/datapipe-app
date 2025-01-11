VERSION := $(shell poetry version -s)

build-example:
	docker build -f example/Dockerfile .

build-frontend:
	docker run --rm -v ${CURDIR}/frontend:/app -v ${CURDIR}/datapipe_app/frontend:/app/build -w /app node:18.7.0-slim yarn
	docker run --rm -v ${CURDIR}/frontend:/app -v ${CURDIR}/datapipe_app/frontend:/app/build -w /app node:18.7.0-slim yarn build

build: build-frontend
	poetry build

lint:
	black --line-length=120 datapipe_app example
	flake8 --max-line-length=120 datapipe_app
	mypy -p datapipe_app --ignore-missing-imports --follow-imports=silent --namespace-packages

release: build
	git commit -am "Release v$(VERSION)"
	git tag "v$(VERSION)"
	git push origin "v$(VERSION)"
	poetry build
	poetry publish
