# Odpad scraper

Dockerized scraper that generates and serves an auto-updating ICS calendar for waste collection.

The container:

- fetches the waste collection schedule on startup
- refreshes the ICS calendar daily at 03:00
- serves the calendar and a small subscription page on port `8080`

## Configuration

Set the source page with `ODPAD_URL`:

```sh
export ODPAD_URL=https://www.trstany.sk/zivot-v-obci/odvoz-odpadu
```

The generated calendar is available at:

```text
/odvoz-odpadu.ics
```

## Docker

Build and run locally:

```sh
docker build -t odpad-scraper .

mkdir -p ./test-data
docker run --rm \
  --name odpad-scraper \
  -e ODPAD_URL \
  -p 8080:8080 \
  -v "$PWD/test-data:/data" \
  odpad-scraper
```

The image healthcheck verifies that the HTTP server responds and that the
generated calendar contains at least one event and a closing `END:VCALENDAR`.
Check the container status in another terminal:

```sh
docker inspect --format '{{json .State.Health}}' odpad-scraper
```

For local script execution outside Docker, set both variables explicitly:

```sh
ODPAD_OUTPUT="$PWD/odvoz-odpadu.ics" \
python3 scrape_odpad.py
```

## Published image

GitHub Actions publishes the image to GHCR on repository changes:

```text
ghcr.io/pduchnovsky/odpad-scraper:latest
```

The workflow is located at `.github/workflows/generate-image.yml`.

## Compose

Use the published image in Docker Compose:

```yaml
image: ghcr.io/pduchnovsky/odpad-scraper:latest
environment:
  - TZ=Europe/Amsterdam
  - ODPAD_URL=${ODPAD_URL:?ODPAD_URL must be set}
volumes:
  - /volume1/docker/odpad:/data
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
```
