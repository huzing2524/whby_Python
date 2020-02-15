FROM python:3.6

ENV PG_DATABASE="dsd" \
    PG_USER="postgres" \
    PG_PASSWORD="123456" \
    PG_HOST="120.0.0.1" \
    PG_PORT="5432" \
    REDIS_HOST="127.0.0.1" \
#    REDIS_PORT="6379" \
    REDIS_DATABASE="1" \
    SETTING_NAME="test"

RUN mkdir -p /whby

RUN apt-get update && \
    apt-get install -y \
	supervisor &&\
	rm -rf /var/lib/apt/lists/*

COPY supervisor-app.conf /etc/supervisor/conf.d/

COPY . /whby

WORKDIR /whby

RUN pip3 install -r requirements.txt

EXPOSE 8000

CMD ["supervisord", "-n"]
