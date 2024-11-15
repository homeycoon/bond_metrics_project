FROM apache/airflow:slim-2.10.2-python3.10

RUN airflow db init
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" lxml requests
ADD ./dags/load_bond_data.py /opt/airflow/dags
ENTRYPOINT ["airflow", "standalone"]
