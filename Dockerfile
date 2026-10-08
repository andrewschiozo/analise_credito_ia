FROM python:3.14-slim

WORKDIR /app

ARG INSTALL_DEV=false

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt requirements-dev.txt ./

RUN if [ "$INSTALL_DEV" = "true" ] ; then \
        pip install --no-cache-dir -r requirements-dev.txt ; \
    else \
        pip install --no-cache-dir -r requirements.txt ; \
    fi

COPY . .