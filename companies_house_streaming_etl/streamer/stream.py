#  Copyright 2024 HM Revenue & Customs

import requests
import boto3
import smart_open
import orjson
import logging
from datetime import datetime, timedelta
import time

from companies_house_streaming_etl import SettingsLoader, Settings
from companies_house_streaming_etl.local_config.local_conf import data_directory


class RateLimited(Exception):
    pass


class LambdaWillExpireSoon(Exception):
    pass


def stream(stream_settings: Settings, channel: str, debug_mode: bool):
    created_session = requests.session()  # TODO: use tenacity.retry()

    url = stream_settings.api_url + channel + "?timepoint=" + read_timepoint(stream_settings)

    auth_header = {
        "authorization": f"Basic {stream_settings.encoded_key}"
    }

    write_path = data_directory(stream_settings) + "/" + str(int(time.time()))  # filenames by epoch second

    response_count = 0
    latest_timepoint = 0  # used to keep track of where to continue when re-connecting
    # Lambda max runtime is 900s, assume 200s required to start streaming and write to s3 after done
    max_allowed_time = datetime.now() + timedelta(seconds=30)

    try:
        with created_session.get(url, headers=auth_header, stream=True) as api_responses:
            if api_responses.status_code == 429:
                raise RateLimited
            elif api_responses.status_code == 200:
                with smart_open.open(write_path, 'wb') as file_out:
                    for response in api_responses.iter_lines():
                        if datetime.now() > max_allowed_time:
                            logging.info("lambda will time out, restart instead")
                            created_session.close()
                            raise LambdaWillExpireSoon
                        else:
                            if debug_mode:
                                logging.info(
                                    f"time not yet up, currently have this much remaining: {max_allowed_time - datetime.now()}")
                        if response and (response != "\n"):
                            response_count += 1
                            if debug_mode:
                                logging.info(response)
                            file_out.write(response)
                            file_out.write(b"\n")
                            response_timepoint = orjson.loads(response)["event"]["timepoint"]
                            if response_timepoint > latest_timepoint:
                                latest_timepoint = response_timepoint
            else:
                logging.error(f"non-200 status code: {api_responses.status_code}")
                raise ConnectionError
    except LambdaWillExpireSoon:
        logging.info("timed out to start a new lambda")
        logging.info(f"number of responses from {channel} written to s3: {response_count}")
        logging.info(f"new latest timepoint: {latest_timepoint}")
        # write updated timepoint file
        write_timepoint(stream_settings, str(latest_timepoint))
    except RateLimited:
        logging.error("status code 429 we are rate limited - hold off until next scheduled lambda")


def write_timepoint(settings: Settings, timepoint: str):
    if settings.write_location == "s3":
        s3 = boto3.resource('s3')
        s3.Object(settings.write_bucket, settings.write_prefix + "/timepoint").put(Body=timepoint)
    elif settings.write_location == "local":
        with open(data_directory(settings) + "/timepoint", "w+") as timepoint_file:
            timepoint_file.write(timepoint)
    else:
        raise NotImplementedError


def read_timepoint(settings: Settings) -> str:
    if settings.write_location == "s3":
        s3 = boto3.resource('s3')
        return str(s3.Object(settings.write_bucket, settings.write_prefix + "/timepoint").get()['Body'].read())
    elif settings.write_location == "local":
        with open(data_directory(settings) + "/timepoint", "r") as timepoint_file:
            return timepoint_file.read()
    else:
        raise NotImplementedError


def start_streaming(_, _2):
    """
    Connect to the streaming api with timepoint and store all valid responses in a list for 700s (lambda timeout is 900)
    Write to S3 as we go
    keep track of the latest [event][timepoint]
    write to s3 (a file named after the latest timepoint and new line delimited with all responses)
    update a timepoint file to contain the latest timepoint

    :return:
    """
    settings = SettingsLoader.load_settings()

    channel = "companies"  # TODO include more channels

    if settings.debug_mode == "true":
        logging.basicConfig(level=logging.DEBUG)
        debug_mode = True
    else:
        debug_mode = False

    stream(settings, channel, debug_mode)
