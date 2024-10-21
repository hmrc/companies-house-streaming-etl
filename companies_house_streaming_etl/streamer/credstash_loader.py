#  Copyright 2024 HM Revenue & Customs

import logging

import credstash


class CredstashLoader:
    @property
    def companies_house_streaming_api_key(self) -> str:
        return self._get_secret("companies_house", "companies_house_streaming_api_key")

    @staticmethod
    def _get_secret(role: str, secret_name: str, profile_name: str = None) -> str:
        logging.info(f"Getting secret %s from Credstash", secret_name)
        return credstash.getSecret(
            name=secret_name, context={"role": role}, profile_name=profile_name
        )
