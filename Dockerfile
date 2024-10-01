FROM ghcr.io/apeworx/silverback:latest

USER root

WORKDIR /app

RUN mkdir -p /data
RUN chown harambe:harambe /data

RUN mkdir -p ./.silverback-sessions
RUN chown harambe:harambe ./.silverback-sessions

USER harambe

COPY --chown=harambe:harambe ./bots/* ./bots/

COPY ape-config.yaml .
COPY requirements.txt .
RUN pip install --upgrade pip \
  && pip install -r requirements.txt

run ape plugins install .

ENV WORKERS=1
ENV MAX_EXCEPTIONS=3
