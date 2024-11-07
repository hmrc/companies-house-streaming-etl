# #  Copyright 2024 HM Revenue & Customs
#
# import logging
#
# import credstash
#
#
# class CredstashLoader:
#     @property
#     def companies_house_streaming_api_key(self) -> str:
#         secret = self._get_secret("companies_house", "companies_house_streaming_api_key")
#         log_info_if_debug(f"secret: {secret}", True)  # TODO: Remove in prod
#         log_info_if_debug(secret, True)
#         log_info_if_debug(str(secret), True)
#         return secret
#
#     @staticmethod
#     def _get_secret(role: str, secret_name: str, profile_name: str = None) -> str:
#         log_info_if_debug(f"Getting secret {secret_name} from Credstash", True)
#         return credstash.getSecret(
#             name=secret_name, context={"role": role}, profile_name=profile_name
#         )
#
#
# def log_info_if_debug(log_string: str, debug: bool):
#     if debug:
#         logger = logging.getLogger(__name__)
#         logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
#                             force=True,
#                             datefmt='%Y-%m-%d  %H:%M:%S')
#         logger.info(log_string)
