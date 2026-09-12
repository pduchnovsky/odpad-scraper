# Odpad scraper

Small Docker service that turns a public waste-collection schedule into an
auto-updating ICS calendar.

## What it does

- Fetches and parses the configured source page when the container starts.
- Refreshes the calendar every day at `03:00` container time.
- Keeps the last valid calendar if fetching or parsing fails.
- Replaces the calendar atomically after a successful parse.
- Serves a subscription page and the calendar over HTTP on port `8080`.

The calendar is available at `/odvoz-odpadu.ics`.

## Configuration

`ODPAD_URL` is required. It must be an `http://` or `https://` URL.

```sh
export ODPAD_URL=https://www.trstany.sk/zivot-v-obci/odvoz-odpadu
```

The output path defaults to `/data/odvoz-odpadu.ics`. For local script runs it
can be changed with `ODPAD_OUTPUT`.

## Run locally

Build the image and run it with persistent output data:

```sh
docker build -t odpad-scraper .
mkdir -p test-data
docker run --rm \
  --name odpad-scraper \
  --env ODPAD_URL \
  --publish 8080:8080 \
  --volume "$PWD/test-data:/data" \
  odpad-scraper
```

Open `http://localhost:8080/` or download the calendar from
`http://localhost:8080/odvoz-odpadu.ics`.

Check the container health from another terminal:

```sh
docker inspect --format '{{.State.Health.Status}}' odpad-scraper
```

Run the Python script directly, without Docker:

```sh
ODPAD_OUTPUT="$PWD/odvoz-odpadu.ics" python3 scrape_odpad.py
```

Install the dependencies first if they are not already available:

```sh
python3 -m pip install requests beautifulsoup4
```

## Published image

GitHub Actions builds and publishes the image to GHCR when image-related files
change. The workflow is `.github/workflows/generate-image.yml`.

```text
ghcr.io/pduchnovsky/odpad-scraper:latest
```

## Compose

Example service configuration:

```yaml
odpad:
  image: ghcr.io/pduchnovsky/odpad-scraper:latest
  container_name: odpad
  environment:
    - TZ=Europe/Amsterdam
    - ODPAD_URL=${ODPAD_URL:?ODPAD_URL must be set}
  volumes:
    - /volume1/docker/odpad:/data
  security_opt:
    - no-new-privileges:true
  cap_drop:
    - ALL
  restart: always
```

The persistent `/data` volume preserves the last valid calendar across
container recreation. The source URL should be stored in the deployment
environment or `.env` file, not committed to the repository.

## Calendar auto-update workflow

`.github/workflows/update-calendar.yml` runs the scraper directly on GitHub
Actions (daily, plus manual dispatch) and commits `odvoz-odpadu.ics` back to
the repository if it changed. This keeps a working copy of the calendar in
the repo independent of any running container.

It requires an `ODPAD_URL` repository variable (not a secret, it's public)
pointing to the source page.

Subscribe directly to the committed file (calendar apps re-fetch this URL on
their own schedule):

```text
https://raw.githubusercontent.com/pduchnovsky/odpad-scraper/main/odvoz-odpadu.ics
```

Some calendar apps (Apple Calendar, Outlook) recognize `webcal://` links and
subscribe automatically instead of doing a one-off import:

```text
webcal://raw.githubusercontent.com/pduchnovsky/odpad-scraper/main/odvoz-odpadu.ics
```
