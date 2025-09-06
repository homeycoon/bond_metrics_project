from airflow.decorators import dag, task
from datetime import timedelta
import requests

from logger import logger

default_args = {
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}


@dag(default_args=default_args, schedule_interval="0 5 * * *", catchup=False)
def load_data_airflow():
    """
    Даг для загрузки первичной информации
    по облигациям и валютам

    :return: None
    """
    @task()
    def load_currency():
        """
        Task для загрузки первичных данных по валютам

        :return: None
        """
        try:
            result = requests.get('http://app:8000/update/currencies')
            logger.info(result)
        except requests.exceptions.RequestException as e:
            logger.error(str(e))

    @task()
    def load_bonds():
        """
        Task для загрузки первичных данных по облигациям

        :return: None
        """
        try:
            result = requests.get('http://app:8000/update/bonds')
            logger.info(result)
        except requests.exceptions.RequestException as e:
            logger.error(str(e))


load_data_airflow = load_data_airflow()
