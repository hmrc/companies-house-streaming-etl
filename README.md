
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

### Create a file at `target/data-outputs/timepoint` with the starting timepoint
You can get the current CH stream timepoint by calling the service or choose one in the past from the latest bulk data.
Note: this is not epoch-time!
It should look something like this:

```timepoint
86718982
```

Install poetry dependencies with:
```bash
poetry install
```

### If you want to run without docker:

In a terminal, run the streamer by executing the following:
```bash
CH_DEBUG="true" CH_WRITE_LOCATION="local" CH_WRITE_BUCKET="n/a" CH_WRITE_PREFIX="n/a" poetry run run-streamer
```

### if you want to run with Docker (useful for testing lambda deployment)

#### If dependencies have changed
Ensure that the requirements file has been updated too (this is done to avoid complications with poetry in docker)
```bash
make create-requirements-txt
```

make the docker image
```bash
make build
```

run the docker image in a container
```bash
make run-local
```

### License

This code is open source software licensed under the [Apache 2.0 License]("http://www.apache.org/licenses/LICENSE-2.0.html").