
# companies-house-streaming-etl

Proof of concept for use of the Companies House Streaming API to be integrated with our ETL

- See API documentation [here](https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference)

## Before merging a PR and publishing with Jenkins
Ensure the dependencies have been updated, see [here](#if-dependencies-have-changed)
Increment `.version` to create an updated version tag in ECR

## To run the streamer locally:

### First get an API key:

- Follow instruction [here](https://developer-specs.company-information.service.gov.uk/streaming-api/guides/authentication) to create an account
- Make a new application and find the key in the `manage-applications` page

### Create a yaml file at `companies_house_streaming_etl/config.yml` it should like this with your api key 

```yaml
stream_key: ...
```

- `stream_key` Your api key obtained following the instructions above

First please make sure that you:
* are using the Python version specified in [.python-version](.python-version)
* have the [Poetry](https://python-poetry.org/) Python dependency manager installed by following instructions
  [here](https://python-poetry.org/docs/#osx--linux--bashonwindows-install-instructions)

Install poetry dependencies with:
```bash
poetry install
```

### If you want to run without docker:

In a terminal, run the streamer by executing the following:
```bash
CH_WRITE_MODE="hudi" CH_WRITE_LOCATION="local" CH_WRITE_BUCKET="n/a" poetry run run-streamer
```

View hudi table downloaded locally with:
```bash
CH_WRITE_MODE="hudi" CH_WRITE_LOCATION="local" CH_WRITE_BUCKET="n/a" poetry run view-hudi-data
```

### if you want to run with Docker (useful for testing lambda deployment)

#### If dependencies have changed
Ensure that the requirements file has been updated too
```bash
poetry update
```
```bash
poetry export -f requirements.txt --without-hashes > requirements.txt
```

make the docker image
```bash
make build
```

### License

This code is open source software licensed under the [Apache 2.0 License]("http://www.apache.org/licenses/LICENSE-2.0.html").