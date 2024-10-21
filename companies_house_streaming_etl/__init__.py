#  Copyright 2024 HM Revenue & Customs

import base64
import os

import yaml
import envtoml
from pydantic import BaseModel

from companies_house_streaming_etl.streamer.credstash_loader import CredstashLoader


class Settings(BaseModel):
    encoded_key: str
    api_url: str
    debug_mode: str
    write_location: str
    write_bucket: str
    write_prefix: str


class SettingsLoader:
    @staticmethod
    def load_settings() -> Settings:
        root_dir = PathLoader.root_dir()
        yaml_file_path = f"{root_dir}/config.yml"
        toml_file_path = f"{root_dir}/settings.toml"
        settings = envtoml.load(open(toml_file_path))
        run_settings = Settings(**settings)
        run_settings.debug_mode = os.environ["CH_DEBUG"]
        run_settings.write_location = os.environ["CH_WRITE_LOCATION"]
        run_settings.write_bucket = os.environ["CH_WRITE_BUCKET"]
        run_settings.write_prefix = os.environ["CH_WRITE_PREFIX"]

        if run_settings.write_location == "local":
            run_settings.encoded_key = base64.b64encode(
                    bytes(yaml.safe_load(open(yaml_file_path, 'r').read())['stream_key'] + ':',
                          'utf-8')
                ).decode('utf-8')
        else:
            credstash_loader = CredstashLoader
            run_settings.encoded_key = credstash_loader.companies_house_streaming_api_key

        return run_settings


class PathLoader:
    @staticmethod
    def root_dir() -> str:
        return os.path.dirname(os.path.abspath(__file__))
