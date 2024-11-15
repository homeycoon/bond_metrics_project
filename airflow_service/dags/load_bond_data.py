from airflow.decorators import dag, task
from datetime import timedelta
import requests


default_args = {
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}


@dag(default_args=default_args, schedule_interval="0 5 * * *", catchup=False)
def load_data_airflow():
    @task()
    def load_currency():
        try:
            result = requests.get('http://app:8000/update/currencies')
            print(result)
        except requests.exceptions.RequestException as e:
            print(e)

    @task()
    def load_bonds():
        try:
            result = requests.get('http://app:8000/update/bonds')
            print(result)
        except requests.exceptions.RequestException as e:
            print(e)


load_data_airflow = load_data_airflow()
