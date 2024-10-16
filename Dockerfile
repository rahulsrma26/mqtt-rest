FROM python:3.11-alpine

RUN pip install poetry

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN touch README.md

RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

COPY mqtt_rest ./mqtt_rest

RUN poetry install --without dev

ENV SERVER_IP 0.0.0.0
ENV SERVER_PORT 9000
ENV SERVER_LOG_LEVEL "info"
ENV BROKER_IP ""
ENV BROKER_PORT 1883
ENV MQTT_USER ""
ENV MQTT_PASS ""
ENV MQTT_LOG ""

ENTRYPOINT ["poetry", "run", "python", "-m", "mqtt_rest.run"]
