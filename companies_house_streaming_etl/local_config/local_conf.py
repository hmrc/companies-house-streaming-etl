#  Copyright 2024 HM Revenue & Customs
import os
from pathlib import Path
from typing import Optional

import wget
import logging
from pyspark.sql import SparkSession

from companies_house_streaming_etl import PathLoader


def local_working_directory_creator() -> Path:
    project_directory = Path(PathLoader.root_dir())
    working_directory = project_directory.joinpath(
        "target", "data-outputs"
    )
    working_directory.mkdir(parents=True, exist_ok=True)
    return working_directory


def jars_directory() -> Path:
    local_working_directory = local_working_directory_creator()
    local_jars_directory = local_working_directory / "jars"
    local_jars_directory.mkdir(exist_ok=True)
    return local_jars_directory


def data_directory() -> str:
    write_location = os.environ["CH_WRITE_LOCATION"]

    if write_location == "s3":
        return "s3 link here"  # TODO put the link here
    elif write_location == "local":
        local_working_directory = local_working_directory_creator()
        local_jars_directory = local_working_directory / "data"
        local_jars_directory.mkdir(exist_ok=True)
        return str(local_jars_directory)


def attempt_to_download_file(url: str, output_directory: Path) -> Optional[Path]:
    try:
        filepath: str = wget.download(url=url, out=str(output_directory))  # type: ignore
        return Path(filepath)
    except:
        return None


def download_hudi_jar(hudi_version: str, jars_directory: Path, spark_version) -> Path:
    file_path = f"hudi-spark{spark_version}-bundle_2.12-{hudi_version}.jar"
    full_file_path = jars_directory / file_path

    if full_file_path.exists():
        logging.info("Hudi jar already available")
        return full_file_path
    else:
        logging.info("Hudi jar will be downloaded")

    jar_file = attempt_to_download_file(
        f"https://repo1.maven.org/maven2/org/apache/hudi/hudi-spark{spark_version}-bundle_2.12/{hudi_version}/{file_path}",
        jars_directory,
    )

    if jar_file:
        logging.info("Hudi jar download complete")
        return jar_file

    raise RuntimeError("Couldn't download hudi jar")


def create_local_spark_session(
        hudi_version: str,
        spark_version: str
) -> SparkSession:
    hudi_jar = str(download_hudi_jar(hudi_version, jars_directory(), spark_version))

    extra_jars = [hudi_jar]
    extra_class_path = ":".join(extra_jars)
    config = (
        SparkSession.builder.master("local[2]")
        .appName("localRun")
        .config("spark.driver.extraClassPath", extra_class_path)
        .config('spark.serializer', 'org.apache.spark.serializer.KryoSerializer')
    )
    return config.getOrCreate()
