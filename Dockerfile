FROM python:3.7-slim
ENV PIP_NO_CACHE_DIR=1
ADD docker_hosts/ /app/docker_hosts
ADD docker/run.sh /app
ADD requirements.txt /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT ["/app/run.sh"]
