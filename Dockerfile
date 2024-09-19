FROM python:3.11 AS base

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Create virtualenv using poetry lockfile
FROM base AS builder

FROM apeworx/silverback:latest

USER root
RUN apt-get -y update && apt-get -y install git

# Is this necessary after a real tagged release?
ENV SETUPTOOLS_SCM_PRETEND_VERSION="6.6.6"

ENV PIP_NO_CACHE_DIR=off \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.6.1

WORKDIR /app

RUN mkdir -p /data
RUN chown harambe:harambe /data

USER harambe

COPY --chown=harambe:harambe ./bots/* ./bots/

COPY ape-config.yaml .
COPY requirements.txt .
RUN pip install --upgrade pip \
  && pip install -r requirements.txt

ENV WORKERS=1
ENV MAX_EXCEPTIONS=3