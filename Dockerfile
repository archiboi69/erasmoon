# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12.0

FROM python:${PYTHON_VERSION}-slim

LABEL fly_launch_runtime="flask"

WORKDIR /code

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 8080

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=8080"]

# For alpine-based images:
RUN apk add ca-certificates fuse3 sqlite

# For debian/ubuntu-based images (uncomment if needed):
# RUN apt-get update -y && apt-get install -y ca-certificates fuse3 sqlite3

# Install LiteFS
COPY --from=flyio/litefs:0.5 /usr/local/bin/litefs /usr/local/bin/litefs

COPY litefs.yml /etc/litefs.yml
