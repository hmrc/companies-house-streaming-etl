ECR_URL=727065427295.dkr.ecr.eu-west-2.amazonaws.com
IMAGE_NAME=cip-insights-reputation/companies-house-streaming-lambda
TEST_IMAGE_NAME=$(IMAGE_NAME)-test
SHELL=/bin/bash

version_file := .version
VERSION := 1.0.3.lamda.insights

build:
	docker build --platform linux/amd64 --file Dockerfile -t $(IMAGE_NAME) .

# only used for local testing
run-local:
	docker run --env CH_DEBUG="true" --env CH_WRITE_LOCATION="local" --env CH_WRITE_BUCKET="n/a" --env CH_WRITE_PREFIX="n/a" -i $(IMAGE_NAME)
create-requirements-txt:
	poetry update
	poetry install
	poetry export -f requirements.txt --without-hashes > unusedrequirements.txt
	sed 's/;.*//' unusedrequirements.txt > requirements.txt # remove python version requirement set by poetry (causing issues in CI)
	rm unusedrequirements.txt

# tests currently not implemented
#test-build:
#	docker build --file Dockerfile --target test -t $(TEST_IMAGE_NAME) .
#
#test: test-build
#	docker run \
#	--entrypoint /bin/sh \
#	$(TEST_IMAGE_NAME) \
#	-c "python -m pytest -o log_cli=true tests"
#
#ci/check-fmt:
#	docker run --rm --volume $(WORKSPACE):/code --workdir /code $(BLACK_IMAGE) black --check companies_house_streaming_etl tests/

ci/build: .version build

# tests currently not implemented
#ci/test: test

ci/publish:
	aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 727065427295.dkr.ecr.eu-west-2.amazonaws.com

	docker tag $(IMAGE_NAME) $(IMAGE_NAME):v$(VERSION)
	docker tag $(IMAGE_NAME) $(ECR_URL)/$(IMAGE_NAME):v$(VERSION)
	docker push $(ECR_URL)/$(IMAGE_NAME):v$(VERSION)

ci/release: ci/publish
