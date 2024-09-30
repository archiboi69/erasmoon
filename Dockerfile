# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12.0

FROM python:${PYTHON_VERSION}-slim

LABEL fly_launch_runtime="flask"

WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    fuse3 \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install LiteFS
COPY --from=flyio/litefs:0.5 /usr/local/bin/litefs /usr/local/bin/litefs

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 8080

# Copy language data
COPY ./data/europeans_and_their_languages_2024_summed.csv /code/data/

# Use LiteFS as the entrypoint
ENTRYPOINT litefs mount