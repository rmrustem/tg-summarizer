FROM docker.io/python:3.12-slim-bookworm

WORKDIR /app

ADD . .

RUN pip install poetry && poetry sync 

ENTRYPOINT poetry run python -m summarizer
