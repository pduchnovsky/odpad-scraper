# Odpad scraper

Small auto-updating ICS calendar for Trstany, Slovakia. GitHub Actions runs the
scraper daily, commits the generated calendar, and publishes the static
subscription page with GitHub Pages. The parser is only tested against that
source page, so pointing `ODPAD_URL` at another municipality's page is not
guaranteed to work without adjusting `scrape_odpad.py`.

Subscription page:

[https://odpad.duchnovsky.com](https://odpad.duchnovsky.com)

## What it does

- Fetches and parses the configured source page in GitHub Actions.
- Refreshes the calendar every day at `04:00` UTC.
- Keeps the last valid calendar if fetching or parsing fails.
- Replaces the committed calendar only after a successful parse.
- Deploys the subscription page and calendar with GitHub Pages.

The calendar is available at `/odvoz-odpadu.ics`.

The scraper uses the Trstany source page by default. `ODPAD_URL` is optional
and can override it when running the script locally. `ODPAD_OUTPUT` changes the
output path.

## Run locally

Run the scraper directly:

```sh
ODPAD_OUTPUT="$PWD/odvoz-odpadu.ics" python3 scrape_odpad.py
```

Install the dependencies first if they are not already available:

```sh
python3 -m pip install requests beautifulsoup4
```

## GitHub Pages deployment

`.github/workflows/deploy-pages.yml` publishes `index.html` and
`odvoz-odpadu.ics` after changes to the main branch. In the repository settings,
set **Pages → Build and deployment → Source** to **GitHub Actions** once before
the first deployment.

Calendar subscription URL:

[https://odpad.duchnovsky.com/odvoz-odpadu.ics](https://odpad.duchnovsky.com/odvoz-odpadu.ics)

Some calendar apps recognize the equivalent `webcal://` link:

[webcal://odpad.duchnovsky.com/odvoz-odpadu.ics](webcal://odpad.duchnovsky.com/odvoz-odpadu.ics)

## Calendar auto-update workflow

`.github/workflows/update-calendar.yml` runs the scraper directly on GitHub
Actions (daily, plus manual dispatch) and commits `odvoz-odpadu.ics` back to
the repository if it changed.

The public Trstany source URL is the scraper's default, so no repository secret
or variable configuration is needed to run it.

The configured custom domain is the primary subscription URL for the calendar.
