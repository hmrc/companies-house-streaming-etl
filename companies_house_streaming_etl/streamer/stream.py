#  Copyright 2024 HM Revenue & Customs

import requests
import boto3
import smart_open
import orjson
import logging
from datetime import datetime, timedelta
from typing import Any, Dict
from requests.exceptions import ChunkedEncodingError

from companies_house_streaming_etl import SettingsLoader, Settings
from companies_house_streaming_etl.local_config.local_conf import data_directory


class RateLimited(Exception):
    pass


class LambdaWillExpireSoon(Exception):
    pass


def stream(stream_settings: Settings, channel: str, debug_mode: bool):
    log_info_if_debug(f"creating session", debug_mode)
    created_session = requests.session()

    current_timepoint = read_timepoint(stream_settings, channel)

    logging.warning(f"starting from timepoint: ${current_timepoint}")

    url = stream_settings.api_url + channel + "?timepoint=" + current_timepoint
    log_info_if_debug(f"url: {url}", debug_mode)

    auth_header = {
        "authorization": f"Basic {stream_settings.encoded_key}"
    }

    response_count = 0
    latest_timepoint = 0  # used to keep track of where to continue when re-connecting
    # Lambda max runtime is 900s, assume 300s required to start streaming and write to s3 after done
    max_allowed_time = datetime.now() + timedelta(seconds=600)
    logging.warning(f"max allowed time: {max_allowed_time}")

    try:
        with created_session.get(url, headers=auth_header, stream=True) as api_responses:
            log_info_if_debug(f"response status code: {api_responses.status_code}", debug_mode)
            if api_responses.status_code == 429:
                raise RateLimited
            if api_responses.status_code == 416:
                logging.error(f"the requested timepoint is too old - (use new bulk data timepoint instead)")
                raise ConnectionError
            elif api_responses.status_code == 200:
                try:
                    for response in api_responses.iter_lines():
                        if datetime.now() > max_allowed_time:
                            log_info_if_debug("lambda will time out, restart instead", True)
                            created_session.close()
                            raise LambdaWillExpireSoon
                        if response and (response == "\n" or response == b'' or response == b'\n'):
                            logging.warning("heartbeat received from API")
                        if response and (response != "\n"):
                            response_count += 1
                            response_timepoint = orjson.loads(response)["event"]["timepoint"]
                            # writing individually instead of streaming - exception causes no data written to s3
                            #   possible (smart_open bug)
                            with smart_open.open(data_directory(stream_settings) + f"/{channel}" + "/data/" + str(response_timepoint),
                                                 'wb') as file_out:
                                file_out.write(response)
                            if response_timepoint > latest_timepoint:
                                latest_timepoint = response_timepoint
                except ChunkedEncodingError as ex:
                    logging.warning(f"Invalid chunk encoding {str(ex)}")
                    logging.warning("ChunkedEncodingError, writing what we have so far even though time remaining")
                    raise LambdaWillExpireSoon
            else:
                logging.error(f"non-200 status code: {api_responses.status_code}")
                raise ConnectionError
    except LambdaWillExpireSoon:
        logging.warning("timed out to start a new lambda")
        logging.warning(f"number of responses from {channel} written to s3: {response_count}")
        logging.warning(f"new latest timepoint: {latest_timepoint}")
        # write updated timepoint file
        write_timepoint(stream_settings, str(latest_timepoint), channel)
    except RateLimited:
        logging.error("status code 429 we are rate limited - hold off until next scheduled lambda")


def write_timepoint(settings: Settings, timepoint: str, channel: str):
    if settings.write_location == "s3":
        s3 = boto3.client('s3')
        s3.put_object(Body=timepoint, Bucket=settings.write_bucket,
                      Key=settings.write_prefix + f"/{channel}" + "/timepoint")
    elif settings.write_location == "local":
        with open(data_directory(settings) + f"/{channel}" + "/timepoint", "w+") as timepoint_file:
            timepoint_file.write(timepoint)
    else:
        raise NotImplementedError


def read_timepoint(settings: Settings, channel: str) -> str:
    if settings.write_location == "s3":
        s3 = boto3.resource('s3')
        return str(
            s3.Object(settings.write_bucket, settings.write_prefix + f"/{channel}" + "/timepoint").get()[
                'Body'].read().decode('utf-8'))
    elif settings.write_location == "local":
        with open(data_directory(settings) + f"/{channel}" + "/timepoint", "r") as timepoint_file:
            return timepoint_file.read()
    else:
        raise NotImplementedError


def log_info_if_debug(log_string: str, debug: bool):
    if debug:
        logger = logging.getLogger(__name__)
        logger.info(log_string)


def start_streaming(event: Dict[Any, Any] = {"channel": "companies"}, _=""):
    """
    Connect to the streaming api with timepoint and store all valid responses for 600s (lambda timeout is 900)
    Write to S3 as we go
    keep track of the latest [event][timepoint]
    update a timepoint file to contain the latest timepoint
    :param event: Dict containing channel type see available channels here:
        https://developer-specs.company-information.service.gov.uk/api.ch.gov.uk-specifications/swagger-2.0/spec/streaming.json
        (default channel parameter is 'companies' for local testing)
    :param _: Context parameter not used
    """
    logger = logging.getLogger(__name__)
    settings = SettingsLoader.load_settings()

    if settings.debug_mode == "true":
        debug_mode = True
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
                            force=True,
                            datefmt='%Y-%m-%d  %H:%M:%S')
        logger.info("debug mode set")
    else:
        debug_mode = False
        # Setting log level to warning in non-debug mode to avoid extensive smart-open logs (INFO level)
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING,
                            force=True,
                            datefmt='%Y-%m-%d  %H:%M:%S')

    logger.warning("event:")
    logger.warning(event)

    try:
        channel = event["channel"]
    except KeyError:
        raise ValueError('required parameter "channel" not found')

    stream(settings, channel, debug_mode)
