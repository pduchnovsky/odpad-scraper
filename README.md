# Odpad scraper

Dockerized scraper that generates and serves an auto-updating ICS calendar for waste collection in Trstany, Slovakia.

The container:

- fetches the waste collection schedule on startup
- refreshes the ICS calendar daily at 03:00
- serves the calendar and a small subscription page on port `8080`

## Configuration

Set the source page with `ODPAD_URL`:

```sh
ODPAD_URL=https://www.trstany.sk/zivot-v-obci/odvoz-odpadu
```

The generated calendar is available at:

```text
/odvoz-odpadu.ics
```

## Docker

Build and run locally:

```sh
docker build -t odpad-scraper .
docker run --rm \
  -e ODPAD_URL=https://www.trstany.sk/zivot-v-obci/odvoz-odpadu \
  -p 8080:8080 \
  odpad-scraper
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
  - ODPAD_URL=${ODPAD_URL}
```
