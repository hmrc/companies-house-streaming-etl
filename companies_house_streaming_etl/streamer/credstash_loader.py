#  Copyright 2024 HM Revenue & Customs

import logging

import credstash

from companies_house_streaming_etl.streamer.stream import log_info_if_debug


class CredstashLoader:
    @property
    def companies_house_streaming_api_key(self) -> str:
        secret = self._get_secret("companies_house", "companies_house_streaming_api_key")
        log_info_if_debug(f"secret: {secret}", True)  # TODO: Remove in prod
        log_info_if_debug(secret, True)
        log_info_if_debug(str(secret), True)
        return secret

    @staticmethod
    def _get_secret(role: str, secret_name: str, profile_name: str = None) -> str:
        log_info_if_debug(f"Getting secret {secret_name} from Credstash", True)
        return credstash.getSecret(
            name=secret_name, context={"role": role}, profile_name=profile_name
        )
