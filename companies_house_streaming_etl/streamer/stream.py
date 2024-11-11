#  Copyright 2024 HM Revenue & Customs

import requests
import boto3
import smart_open
import orjson
import logging
from datetime import datetime, timedelta

from companies_house_streaming_etl import SettingsLoader, Settings
from companies_house_streaming_etl.local_config.local_conf import data_directory


class RateLimited(Exception):
    pass


class LambdaWillExpireSoon(Exception):
    pass


def stream(stream_settings: Settings, channel: str, debug_mode: bool):
    log_info_if_debug(f"creating session", debug_mode)
    created_session = requests.session()  # TODO: use tenacity.retry()

    url = stream_settings.api_url + channel + "?timepoint=" + read_timepoint(stream_settings)
    log_info_if_debug(f"url: {url}", debug_mode)

    auth_header = {
        "authorization": f"Basic {stream_settings.encoded_key}"
    }

    response_count = 0
    latest_timepoint = 0  # used to keep track of where to continue when re-connecting
    # Lambda max runtime is 900s, assume 300s required to start streaming and write to s3 after done
    max_allowed_time = datetime.now() + timedelta(seconds=600)
    log_info_if_debug(f"max allowed time: {max_allowed_time}", debug_mode)

    try:
        with created_session.get(url, headers=auth_header, stream=True) as api_responses:
            log_info_if_debug(f"response status code: {api_responses.status_code}", debug_mode)
            if api_responses.status_code == 429:
                raise RateLimited
            elif api_responses.status_code == 200:
                for response in api_responses.iter_lines():
                    if datetime.now() > max_allowed_time:
                        log_info_if_debug("lambda will time out, restart instead", True)
                        created_session.close()
                        raise LambdaWillExpireSoon
                    if response and (response == "\n"):
                        log_info_if_debug("heartbeat received from API", debug_mode)
                    if response and (response != "\n"):
                        response_count += 1
                        response_timepoint = orjson.loads(response)["event"]["timepoint"]
                        # writing individually instead of streaming - exception causes no data written to s3
                        #   possible (smart_open bug)
                        with smart_open.open(data_directory(stream_settings) + "/data/" + str(response_timepoint),
                                             'wb') as file_out:
                            file_out.write(response)
                            # file_out.write(b"\n")
                        if response_timepoint > latest_timepoint:
                            # log_info_if_debug(f"new latest timepoint: {response_timepoint}", debug_mode)
                            latest_timepoint = response_timepoint
            else:
                log_info_if_debug(f"non-200 status code: {api_responses.status_code}", True)
                raise ConnectionError
    except LambdaWillExpireSoon:
        log_info_if_debug("timed out to start a new lambda", True)
        log_info_if_debug(f"number of responses from {channel} written to s3: {response_count}", True)
        log_info_if_debug(f"new latest timepoint: {latest_timepoint}", True)
        # write updated timepoint file
        write_timepoint(stream_settings, str(latest_timepoint))
    except RateLimited:
        log_info_if_debug("status code 429 we are rate limited - hold off until next scheduled lambda", True)


def write_timepoint(settings: Settings, timepoint: str):
    if settings.write_location == "s3":
        s3 = boto3.client('s3')
        s3.put_object(Body=timepoint, Bucket=settings.write_bucket, Key=settings.write_prefix + "/timepoint")
    elif settings.write_location == "local":
        with open(data_directory(settings) + "/timepoint", "w+") as timepoint_file:
            timepoint_file.write(timepoint)
    else:
        raise NotImplementedError


def read_timepoint(settings: Settings) -> str:
    if settings.write_location == "s3":
        s3 = boto3.resource('s3')
        return str(
            s3.Object(settings.write_bucket, settings.write_prefix + "/timepoint").get()['Body'].read().decode('utf-8'))
    elif settings.write_location == "local":
        with open(data_directory(settings) + "/timepoint", "r") as timepoint_file:
            return timepoint_file.read()
    else:
        raise NotImplementedError


def log_info_if_debug(log_string: str, debug: bool):
    if debug:
        logger = logging.getLogger(__name__)
        logger.info(log_string)


def start_streaming(_="", _2=""):
    """
    Connect to the streaming api with timepoint and store all valid responses in a list for 700s (lambda timeout is 900)
    Write to S3 as we go
    keep track of the latest [event][timepoint]
    write to s3 (a file named after the latest timepoint and new line delimited with all responses)
    update a timepoint file to contain the latest timepoint

    :return:
    """
    logger = logging.getLogger(__name__)
    settings = SettingsLoader.load_settings()

    channel = "companies"  # TODO include more channels

    if settings.debug_mode == "true":
        debug_mode = True
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
                            force=True,
                            datefmt='%Y-%m-%d  %H:%M:%S')
        logger.info("debug mode set")
    else:
        debug_mode = False
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.ERROR,
                            force=True,
                            datefmt='%Y-%m-%d  %H:%M:%S')

    stream(settings, channel, debug_mode)
