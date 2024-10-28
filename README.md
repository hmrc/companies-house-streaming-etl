
# companies-house-streaming-etl

Proof of concept for use of the Companies House Streaming API to be integrated with our ETL

- See API documentation [here](https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference)

### Steps to get API key:

- Follow instruction [here](https://developer-specs.company-information.service.gov.uk/streaming-api/guides/authentication) to create an account
- Make a new application and find the key in the `manage-applications` page

### Create a yaml file at `companies_house_streaming_etl/config.yml` it should like this with your api key 

```yaml
stream_key: ...
```

- `stream_key` Your api key obtained following the instructions above

### To run the streamer:

First please make sure that you:
* are using the Python version specified in [.python-version](.python-version)
* have the [Poetry](https://python-poetry.org/) Python dependency manager installed by following instructions
  [here](https://python-poetry.org/docs/#osx--linux--bashonwindows-install-instructions)

Install poetry dependencies with:
```bash
poetry install
```

In a terminal, run the streamer by executing the following:
```bash
poetry run run-streamer
```

View hudi table with:
```bash
poetry run view-hudi-data
```

### License

This code is open source software licensed under the [Apache 2.0 License]("http://www.apache.org/licenses/LICENSE-2.0.html").