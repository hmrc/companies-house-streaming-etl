#  Copyright 2024 HM Revenue & Customs

import requests
import json
import logging
from pyspark.sql import SparkSession

from companies_house_streaming_etl import SettingsLoader, Settings
from companies_house_streaming_etl.local_config.local_conf import create_local_spark_session, data_directory


# class CompaniesHouseStream:
#
#     def __init__(self, output_location: str):
#         self.output_location = output_location

def print_consumer(line: str, spark: SparkSession, write_path: str):
    print(json.dumps(json.loads(line), indent=2))


def hudi_consumer(line: str, spark: SparkSession, write_path: str):
    hudi_options = {
        'hoodie.table.name': "CompaniesHouseData",
        'hoodie.datasource.write.recordkey.field': 'resource_uri',
        'hoodie.datasource.write.partitionpath.field': 'resource_kind',
        'hoodie.datasource.write.table.name': "CompaniesHouseData",
        'hoodie.datasource.write.operation': 'upsert',
        'hoodie.datasource.write.precombine.field': 'event.timepoint',
        'hoodie.upsert.shuffle.parallelism': 2,
        'hoodie.insert.shuffle.parallelism': 2,
        'hoodie.datasource.write.reconcile.schema': True
    }
    line_df = spark.read.json(spark.sparkContext.parallelize([json.dumps(json.loads(line))]), multiLine=True)
    line_df.write.format("org.apache.hudi") \
        .options(**hudi_options) \
        .mode("append").save(write_path)  # this should use the s3 link if not local
    # TODO: use hudi streamer instead? - doesn't look like it supports this, only kafka etc


def stream(stream_settings: Settings, channel, consumer, spark: SparkSession):
    created_session = requests.session()

    url_with_channel = stream_settings.api_url + channel

    auth_header = {
        "authorization": f"Basic {stream_settings.encoded_key}"
    }

    write_path = data_directory()

    with created_session.get(url_with_channel, headers=auth_header, stream=True) as api_responses:
        for response in api_responses.iter_lines():
            if response:
                consumer(response, spark, write_path)

    # TODO: handle connection problems:
    #  - for 429s back off and sleep for 2 minutes
    #  - other disconnections, usual retry with an incrementing sleep time
    #  - keep track of last successful response time and use this with ?timepoint=<epoch-seconds> in the url to catch up


def start_streaming():
    settings = SettingsLoader.load_settings()
    local_spark_session = create_local_spark_session(hudi_version=settings.hudi_version, spark_version=settings.spark_version)

    channels = ["companies"]

    match settings.write_mode:
        case "print":
            # TODO: call all the channels in parallel (use multiprocessing) - to do this with the same session
            for channel in channels:
                stream(settings, channel, print_consumer, local_spark_session)
        case "hudi":
            for channel in channels:
                stream(settings, channel, hudi_consumer, local_spark_session)
        case _:
            # TODO: include consumers for postgres, other types?
            raise RuntimeError("Write mode not supported")
