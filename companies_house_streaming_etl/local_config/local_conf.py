#  Copyright 2024 HM Revenue & Customs

import os
from pathlib import Path

from companies_house_streaming_etl import PathLoader, Settings


def local_working_directory_creator() -> Path:
    project_directory = Path(PathLoader.root_dir())
    working_directory = project_directory.joinpath(
        "target", "data-outputs"
    )
    working_directory.mkdir(parents=True, exist_ok=True)
    return working_directory


def data_directory(settings: Settings) -> str:
    write_location = os.environ["CH_WRITE_LOCATION"]

    if write_location == "s3":
        return f"s3://{settings.write_bucket}/{settings.write_prefix}"
    elif write_location == "local":  # only for local testing
        return str(local_working_directory_creator())
