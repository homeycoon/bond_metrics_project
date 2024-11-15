FROM python:3.10-slim

RUN mkdir app
WORKDIR app
ADD requirements.txt /app/
RUN pip install -r requirements.txt
ADD . /app/
CMD alembic upgrade head && python initial_load.py && uvicorn main:app --host 0.0.0.0 --port 8000 --reload