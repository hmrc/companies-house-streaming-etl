#  Copyright 2024 HM Revenue & Customs


from companies_house_streaming_etl import SettingsLoader
from companies_house_streaming_etl.local_config.local_conf import data_directory
from companies_house_streaming_etl.streamer.stream import create_local_spark_session


def display_hudi_table(
        table_name: str = "CompaniesHouseData",
        max_rows: int = 100
):
    settings = SettingsLoader.load_settings()
    local_spark_session = create_local_spark_session(hudi_version=settings.hudi_version,
                                                     spark_version=settings.spark_version)
    hudi_options = {
        'hoodie.table.name': table_name,
    }

    local_spark_session.read.format("org.apache.hudi")\
        .options(**hudi_options)\
        .load(str(data_directory())).show(max_rows, False)
