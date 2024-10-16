#  Copyright 2024 HM Revenue & Customs

import base64
import os

import yaml
import envtoml
from pydantic import BaseModel

from streamer.credstash_loader import CredstashLoader


class Settings(BaseModel):
    encoded_key: str
    api_url: str
    write_mode: str
    write_location: str
    write_bucket: str
    hudi_version: str
    spark_version: str


class SettingsLoader:
    @staticmethod
    def load_settings() -> Settings:
        root_dir = PathLoader.root_dir()
        yaml_file_path = f"{root_dir}/config.yml"
        toml_file_path = f"{root_dir}/settings.toml"
        settings = envtoml.load(open(toml_file_path))
        run_settings = Settings(**settings)
        run_settings.write_mode = os.environ["CH_WRITE_MODE"]
        run_settings.write_location = os.environ["CH_WRITE_LOCATION"]
        run_settings.write_bucket = os.environ["CH_WRITE_BUCKET"]

        if run_settings.write_location == "local":
            run_settings.encoded_key = base64.b64encode(
                    bytes(yaml.safe_load(open(yaml_file_path, 'r').read())['stream_key'] + ':',
                          'utf-8')
                ).decode('utf-8')
        else:
            credstash_loader = CredstashLoader
            run_settings.encoded_key = credstash_loader.companies_house_streaming_api_key
            # run_settings.encoded_key = os.environ["CH_STREAM_KEY"]

        return run_settings

    # TODO: Include credstash loader to get API key from credstash (we will give this lambda access to credstash in tf)


class PathLoader:
    @staticmethod
    def root_dir() -> str:
        return os.path.dirname(os.path.abspath(__file__))
