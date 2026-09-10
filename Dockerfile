FROM python:3.12-alpine

RUN apk add --no-cache busybox-extras \
    && pip install --no-cache-dir requests beautifulsoup4

WORKDIR /app
COPY scrape_odpad.py .

RUN mkdir -p /data \
    && echo "0 3 * * * python3 /app/scrape_odpad.py >> /var/log/cron.log 2>&1" > /etc/crontabs/root

COPY index.html /app/index.html

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
