ECR_URL=727065427295.dkr.ecr.eu-west-2.amazonaws.com
IMAGE_NAME=cip-insights-reputation/companies-house-streaming-etl-lambda
TEST_IMAGE_NAME=$(IMAGE_NAME)-test
SHELL=/bin/bash
BLACK_IMAGE=pyfound/black:23.9.1

version_file := .version
VERSION := $(shell cat ${version_file})

fmt: venv
	docker run --rm --volume $(PWD):/code --workdir /code $(BLACK_IMAGE) black src/ tests/

build:
	docker build --file Dockerfile -t $(IMAGE_NAME) .

# only used for local testing
run-local:
	docker run --env CH_WRITE_MODE="hudi" --env CH_WRITE_LOCATION="local" --env CH_WRITE_BUCKET="n/a" -i $(IMAGE_NAME)

# tests currently not implemented
#test-build:
#	docker build --file Dockerfile --target test -t $(TEST_IMAGE_NAME) .
#
#test: test-build
#	docker run \
#	--entrypoint /bin/sh \
#	$(TEST_IMAGE_NAME) \
#	-c "python -m pytest -o log_cli=true tests"

ci/check-fmt:
	docker run --rm --volume $(WORKSPACE):/code --workdir /code $(BLACK_IMAGE) black --check companies_house_streaming_etl tests/

ci/build: .version build

# tests currently not implemented
#ci/test: test

ci/publish:
	aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 727065427295.dkr.ecr.eu-west-2.amazonaws.com

	docker tag $(IMAGE_NAME) $(IMAGE_NAME):v$(VERSION)
	docker tag $(IMAGE_NAME) $(ECR_URL)/$(IMAGE_NAME):v$(VERSION)
	docker push $(ECR_URL)/$(IMAGE_NAME):v$(VERSION)

ci/release: ci/publish

clean:
	rm -f .version
	docker rmi -f $$(docker images --format '{{.Repository}}:{{.Tag}}' | grep "$(IMAGE_NAME)") || true
	docker rmi -f $(BLACK_IMAGE)